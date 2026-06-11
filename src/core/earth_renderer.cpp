#include "earth_renderer.h"
#include "earth_data.h"
#include <math.h>

#define DEG_TO_RAD 0.017453292519943295769236907684886

EarthRenderer::EarthRenderer(M5GFX* display) : _display(display) {
    _canvas = new LGFX_Sprite(_display);
    _centerX = 120; // Cardputer width 240 / 2
    _centerY = 67;  // Cardputer height 135 / 2
    _earthRadius = 55; // Slightly smaller to fit orbits
}

EarthRenderer::~EarthRenderer() {
    _canvas->deleteSprite();
    delete _canvas;
}

void EarthRenderer::begin() {
    _canvas->createSprite(_display->width(), _display->height());
}

void EarthRenderer::setSunPosition(double subsolarLat, double subsolarLon) {
    _subsolarLat = subsolarLat;
    _subsolarLon = subsolarLon;
    _hasSunData = true;
}

void EarthRenderer::setCameraAttitude(float pitch, float roll, float yaw) {
    _cameraPitch = pitch;
    _cameraRoll = roll;
    _cameraYaw = yaw;
}

// Check if a point is in the day side (angular distance to sun < 90 deg)
bool isDaylight(double lat, double lon, double subLat, double subLon, bool hasSun) {
    if (!hasSun) return true;
    float latR = (float)lat * DEG_TO_RAD;
    float lonR = (float)lon * DEG_TO_RAD;
    float subLatR = (float)subLat * DEG_TO_RAD;
    float subLonR = (float)subLon * DEG_TO_RAD;
    float cos_dist = sinf(subLatR)*sinf(latR) + cosf(subLatR)*cosf(latR)*cosf(lonR - subLonR);
    return cos_dist > 0;
}

// Check if a satellite is in Earth's shadow (cylindrical shadow model)
bool isSatelliteInShadow(double lat, double lon, double alt, double subLat, double subLon, bool hasSun) {
    if (!hasSun) return false;
    float latR = (float)lat * DEG_TO_RAD;
    float lonR = (float)lon * DEG_TO_RAD;
    float subLatR = (float)subLat * DEG_TO_RAD;
    float subLonR = (float)subLon * DEG_TO_RAD;
    
    float cos_theta = sinf(subLatR)*sinf(latR) + cosf(subLatR)*cosf(latR)*cosf(lonR - subLonR);
    if (cos_theta >= 0) return false; // Day side
    
    float r = 6371.0f + (float)alt; // Actual Earth radius + alt (in km)
    float dist_sq = r * r * (1.0f - cos_theta * cos_theta);
    
    // If distance from axis is less than Earth radius, it's eclipsed
    return dist_sq < (6371.0f * 6371.0f);
}

bool EarthRenderer::projectOrthographic(double lat, double lon, double alt, double centerLat, double centerLon, int& outX, int& outY) {
    float latRad = (float)lat * DEG_TO_RAD;
    float lonRad = (float)lon * DEG_TO_RAD;
    float cLatRad = (float)centerLat * DEG_TO_RAD;
    float cLonRad = (float)centerLon * DEG_TO_RAD;

    // Radius scaling: Earth radius + non-linear altitude scale
    float r = _earthRadius;
    if (alt > 0) {
        r += sqrtf((float)alt) * 0.4f; 
    }

    float cos_c = sinf(cLatRad) * sinf(latRad) + cosf(cLatRad) * cosf(latRad) * cosf(lonRad - cLonRad);
    if (cos_c < 0) return false; // Behind the Earth

    float x = r * cosf(latRad) * sinf(lonRad - cLonRad);
    float y = r * (cosf(cLatRad) * sinf(latRad) - sinf(cLatRad) * cosf(latRad) * cosf(lonRad - cLonRad));

    // AR Camera Effect: True 3D Roll (rotating the camera around the forward axis)
    float rollRad = -_cameraRoll * DEG_TO_RAD; // Negative to match natural tilt direction
    float rotatedX = x * cosf(rollRad) - y * sinf(rollRad);
    float rotatedY = x * sinf(rollRad) + y * cosf(rollRad);

    outX = _centerX + (int)rotatedX;
    outY = _centerY - (int)rotatedY;
    return true;
}

void EarthRenderer::drawContinents(double centerLat, double centerLon) {
    // Pre-calculate constants for this frame to save THOUSANDS of CPU cycles
    float cLatRad = (float)centerLat * DEG_TO_RAD;
    float cLonRad = (float)centerLon * DEG_TO_RAD;
    float sin_cLat = sinf(cLatRad);
    float cos_cLat = cosf(cLatRad);
    float rollRad = -_cameraRoll * DEG_TO_RAD;
    float sin_roll = sinf(rollRad);
    float cos_roll = cosf(rollRad);
    
    float subLatR = (float)_subsolarLat * DEG_TO_RAD;
    float subLonR = (float)_subsolarLon * DEG_TO_RAD;
    float sin_subLat = sinf(subLatR);
    float cos_subLat = cosf(subLatR);

    auto drawPath = [&](const float* pts, int count) {
        int prevX = -1, prevY = -1;
        bool prevVisible = false;
        for (int j = 0; j < count; j++) {
            float lat = pts[j*2];
            float lon = pts[j*2+1];
            
            // Inline projection to use precalculated trig
            float latRad = lat * DEG_TO_RAD;
            float lonRad = lon * DEG_TO_RAD;
            float sin_lat = sinf(latRad);
            float cos_lat = cosf(latRad);
            float dLon = lonRad - cLonRad;
            float cos_dLon = cosf(dLon);
            float sin_dLon = sinf(dLon);
            
            float cos_c = sin_cLat * sin_lat + cos_cLat * cos_lat * cos_dLon;
            
            if (cos_c >= 0) {
                float r = (float)_earthRadius;
                float x = r * cos_lat * sin_dLon;
                float y = r * (cos_cLat * sin_lat - sin_cLat * cos_lat * cos_dLon);
                
                float rotatedX = x * cos_roll - y * sin_roll;
                float rotatedY = x * sin_roll + y * cos_roll;
                int outX = _centerX + (int)rotatedX;
                int outY = _centerY - (int)rotatedY;
                
                if (prevVisible) {
                    if (abs(outX - prevX) < 100 && abs(outY - prevY) < 100) {
                        float cos_dist = sin_subLat * sin_lat + cos_subLat * cos_lat * cosf(lonRad - subLonR);
                        bool day = !_hasSunData || cos_dist > 0;
                        uint16_t color = day ? _display->color565(50, 150, 50) : _display->color565(20, 50, 20);
                        _canvas->drawLine(prevX, prevY, outX, outY, color);
                    }
                }
                prevX = outX;
                prevY = outY;
                prevVisible = true;
            } else {
                prevVisible = false;
            }
        }
    };

    for (int i = 0; i < world_map_count; i++) {
        drawPath(world_map[i].points, world_map[i].length);
    }
}

void EarthRenderer::drawEarth(double centerLat, double centerLon, double userLat, double userLon) {
    // Draw Earth circle (darker base for night side feeling)
    _canvas->fillCircle(_centerX, _centerY, _earthRadius, _display->color565(5, 15, 30));
    _canvas->drawCircle(_centerX, _centerY, _earthRadius, _display->color565(30, 60, 100));
    
    // Draw continents
    drawContinents(centerLat, centerLon);
    
    // Draw user location as a map pin 📍
    int ux, uy;
    if (projectOrthographic(userLat, userLon, 0, centerLat, centerLon, ux, uy)) {
        int headX = ux;
        int headY = uy - 6;
        _canvas->fillTriangle(ux, uy, headX - 3, headY + 1, headX + 3, headY + 1, TFT_RED);
        _canvas->fillCircle(headX, headY, 3, TFT_RED);
        _canvas->drawPixel(headX, headY, TFT_WHITE);
    }
    
    // Draw Sun Indicator as a surface decal (shrinks near horizon to look attached)
    if (_hasSunData) {
        int sunX, sunY;
        if (projectOrthographic(_subsolarLat, _subsolarLon, 0, centerLat, centerLon, sunX, sunY)) {
            float cLatRad = (float)centerLat * DEG_TO_RAD;
            float cLonRad = (float)centerLon * DEG_TO_RAD;
            float subLatR = (float)_subsolarLat * DEG_TO_RAD;
            float subLonR = (float)_subsolarLon * DEG_TO_RAD;
            float cos_c = sinf(cLatRad)*sinf(subLatR) + cosf(cLatRad)*cosf(subLatR)*cosf(subLonR - cLonRad);
            
            int r = (int)(8.0f * cos_c); 
            if (r < 1) r = 1;
            
            _canvas->fillCircle(sunX, sunY, r, TFT_YELLOW);
            
            int outerR = (int)(11.0f * cos_c);
            if (outerR > r) {
                _canvas->drawCircle(sunX, sunY, outerR, _display->color565(150, 150, 0));
            }
        }
    }
}

void EarthRenderer::drawSatellite(const SatRenderData& sat, double centerLat, double centerLon) {
    // Draw Orbit
    auto drawOrbit = [&](const std::vector<GeodeticCoord>& orbit, uint16_t baseColor) {
        int prevX = -1, prevY = -1;
        bool prevVisible = false;
        for (const auto& pt : orbit) {
            int x, y;
            bool visible = projectOrthographic(pt.lat, pt.lon, pt.alt, centerLat, centerLon, x, y);
            if (visible && prevVisible) {
                if (abs(x - prevX) < 100 && abs(y - prevY) < 100) {
                    bool shadow = isSatelliteInShadow(pt.lat, pt.lon, pt.alt, _subsolarLat, _subsolarLon, _hasSunData);
                    uint16_t color = shadow ? _display->color565(30, 30, 30) : baseColor;
                    _canvas->drawLine(prevX, prevY, x, y, color);
                }
            }
            prevX = x;
            prevY = y;
            prevVisible = visible;
        }
    };
    
    // Dimmed colors for orbit
    uint16_t pastColor = _display->color565(60, 60, 60);
    uint16_t futureColor = _display->color565(120, 120, 120);
    
    drawOrbit(sat.pastOrbit, pastColor);
    drawOrbit(sat.futureOrbit, futureColor);
    
    // Draw Satellite Current Position
    int sx, sy;
    if (projectOrthographic(sat.currentPos.lat, sat.currentPos.lon, sat.currentPos.alt, centerLat, centerLon, sx, sy)) {
        bool shadow = isSatelliteInShadow(sat.currentPos.lat, sat.currentPos.lon, sat.currentPos.alt, _subsolarLat, _subsolarLon, _hasSunData);
        uint16_t drawColor = shadow ? _display->color565(100, 100, 100) : sat.color;
        
        _canvas->fillCircle(sx, sy, 3, drawColor);
        _canvas->drawCircle(sx, sy, 4, shadow ? _display->color565(50, 50, 50) : TFT_WHITE);
        
        _canvas->setTextColor(drawColor, BLACK);
        _canvas->setTextSize(1);
        _canvas->drawString(sat.name.c_str(), sx + 6, sy - 4);
        
        if (shadow) {
            _canvas->setTextColor(_display->color565(150, 150, 150), BLACK);
            _canvas->drawString("ECLIPSE", sx + 6, sy + 6);
        }
    }
}

void EarthRenderer::render(double centerLat, double centerLon, double userLat, double userLon, const std::vector<SatRenderData>& satellites) {
    static uint32_t lastTime = 0;
    static int frames = 0;
    static int currentFPS = 0;
    
    _canvas->fillSprite(BLACK);
    
    drawEarth(centerLat, centerLon, userLat, userLon);
    
    for (const auto& sat : satellites) {
        drawSatellite(sat, centerLat, centerLon);
    }
    
    frames++;
    uint32_t now = millis();
    if (now - lastTime >= 1000) {
        currentFPS = frames;
        frames = 0;
        lastTime = now;
    }
    
    _canvas->setTextColor(TFT_GREEN, BLACK);
    _canvas->setTextSize(1);
    char fpsStr[16];
    sprintf(fpsStr, "FPS:%d", currentFPS);
    _canvas->drawString(fpsStr, _display->width() - 50, 5);
}

#include "observation_predictor.h"
#include "sgp4_calc.h"
#include "sun_calculator.h"
#include <math.h>

#define DEG_TO_RAD 0.017453292519943295769236907684886
#define RAD_TO_DEG 57.295779513082320876798154814105

ObservationPredictor::ObservationPredictor(double userLat, double userLon, double userAlt) {
    _userLat = userLat;
    _userLon = userLon;
    _userAlt = userAlt;
}

int ObservationPredictor::calculateScore(float maxElevation, float visibleDuration, int baseScore) {
    // Score logic:
    // baseScore is added to the base of 1 star.
    int score = 1 + baseScore; 
    
    // Elevation: > 60 = 3 pts, > 40 = 2 pts, > 20 = 1 pt
    if (maxElevation > 60) score += 3;
    else if (maxElevation > 40) score += 2;
    else if (maxElevation > 20) score += 1;
    
    // Duration: > 300s = 2 pts, > 120s = 1 pt
    if (visibleDuration > 300) score += 2;
    else if (visibleDuration > 120) score += 1;
    
    if (score > 5) score = 5;
    return score;
}

std::vector<PassEvent> ObservationPredictor::predictPasses(const TLEData& tle, uint32_t startTime, int daysToPredict) {
    std::vector<PassEvent> passes;
    
    SGP4Calc sgp4;
    sgp4.init(tle);
    
    SunCalculator sunCalc(nullptr);
    
    uint32_t endTime = startTime + daysToPredict * 24 * 3600;
    uint32_t stepSeconds = 60; // 1 minute step
    
    bool inPass = false;
    PassEvent currentPass;
    
    double userLatRad = _userLat * DEG_TO_RAD;
    double userLonRad = _userLon * DEG_TO_RAD;
    double r_u = 6371.0 + _userAlt;
    
    extern volatile bool triggerPrediction;
    
    int iterations = 0;
    for (uint32_t t = startTime; t <= endTime; t += stepSeconds) {
        if (triggerPrediction) return passes;
        
        iterations++;
        // Reset Watchdog Timer periodically
        // By yielding CPU with vTaskDelay (delay(1) maps to vTaskDelay)
        if (iterations % 100 == 0) {
            vTaskDelay(pdMS_TO_TICKS(5));
        }
        
        double tx, ty, tz;
        if (!sgp4.getTEME(t, tx, ty, tz)) continue;
        
        double gmst = CoordTransform::getGMST(CoordTransform::unixToJulian(t));
        ECEFCoord ecef = CoordTransform::temeToECEF(tx, ty, tz, gmst);
        GeodeticCoord satPos = CoordTransform::ecefToGeodetic(ecef);
        
        // Spherical earth approximation for elevation
        double satLatRad = satPos.lat * DEG_TO_RAD;
        double satLonRad = satPos.lon * DEG_TO_RAD;
        double r_s = 6371.0 + satPos.alt;
        
        double cos_c = sin(userLatRad)*sin(satLatRad) + cos(userLatRad)*cos(satLatRad)*cos(satLonRad - userLonRad);
        double dist2 = r_u*r_u + r_s*r_s - 2.0 * r_u * r_s * cos_c;
        double dist = sqrt(dist2);
        
        double sin_elev = (r_s*r_s - r_u*r_u - dist2) / (2.0 * r_u * dist);
        double el = asin(sin_elev) * RAD_TO_DEG;
        
        // AOS (Acquisition of Signal) threshold: 10 degrees elevation
        if (el >= 10.0) {
            if (!inPass) {
                // New pass starts
                inPass = true;
                currentPass.satName = tle.name;
                currentPass.aosTime = t;
                currentPass.maxElevTime = t;
                currentPass.maxElevation = el;
                currentPass.isVisible = false;
                currentPass.visibleDuration = 0;
            } else {
                // Update max elevation
                if (el > currentPass.maxElevation) {
                    currentPass.maxElevation = el;
                    currentPass.maxElevTime = t;
                }
            }
            
            // 3. Visibility Check
            // Calculate Sun position
            SunPositionData sunPos = sunCalc.calculatePosition(t, _userLat, _userLon);
            
            // User must be in night/twilight (sun altitude < -6 deg)
            bool isNight = (sunPos.altitude < -6.0);
            
            // Satellite must be illuminated by sun (not in Earth's shadow)
            double latR = satPos.lat * DEG_TO_RAD;
            double lonR = satPos.lon * DEG_TO_RAD;
            double subLatR = sunPos.subsolarLat * DEG_TO_RAD;
            double subLonR = sunPos.subsolarLon * DEG_TO_RAD;
            
            double cos_theta = sin(subLatR)*sin(latR) + cos(subLatR)*cos(latR)*cos(lonR - subLonR);
            bool satIlluminated = true;
            if (cos_theta < 0) {
                // Night side, check cylindrical shadow
                double r = 6371.0 + satPos.alt;
                double dist_sq = r * r * (1.0 - cos_theta * cos_theta);
                if (dist_sq < (6371.0 * 6371.0)) {
                    satIlluminated = false; // Eclipsed
                }
            }
            
            if (isNight && satIlluminated) {
                currentPass.isVisible = true;
                currentPass.visibleDuration += stepSeconds;
            }
            
        } else {
            if (inPass) {
                // Pass ends
                inPass = false;
                currentPass.losTime = t;
                
                // Only save the pass if it was visible for some duration
                if (currentPass.isVisible && currentPass.visibleDuration > 60) {
                    currentPass.score = calculateScore(currentPass.maxElevation, currentPass.visibleDuration, tle.baseScore);
                    passes.push_back(currentPass);
                }
            }
        }
    }
    
    return passes;
}

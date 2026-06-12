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
    uint32_t stepSeconds = 60; // Start with 1 minute step
    
    bool inPass = false;
    PassEvent currentPass;
    currentPass.aosTime = 0;
    
    GeodeticCoord observerPos = {_userLat, _userLon, _userAlt};
    
    extern volatile bool triggerPrediction;
    
    int iterations = 0;
    uint32_t t = startTime;
    
    while (t <= endTime) {
        if (triggerPrediction) return passes;
        
        iterations++;
        // Reset Watchdog Timer periodically
        if (iterations % 100 == 0) {
            vTaskDelay(pdMS_TO_TICKS(5));
        }
        
        double tx, ty, tz;
        if (!sgp4.getTEME(t, tx, ty, tz)) {
            t += stepSeconds;
            continue;
        }
        
        double gmst = CoordTransform::getGMST(CoordTransform::unixToJulian(t));
        ECEFCoord ecef = CoordTransform::temeToECEF(tx, ty, tz, gmst);
        
        TopocentricCoord topo = CoordTransform::ecefToTopocentric(observerPos, ecef);
        double el = topo.el;
        
        // Atmospheric refraction compensation for low elevations
        if (el > -5.0 && el < 15.0) {
            double r = 1.02 / tan((el + 10.3 / (el + 5.11)) * DEG_TO_RAD);
            el += r / 60.0;
        }
        
        if (!inPass) {
            if (el >= 0.0 && stepSeconds > 1) {
                // Satellite rose above horizon, rewind and switch to 1-second fine step
                t -= stepSeconds;
                stepSeconds = 1;
                continue;
            }
            
            if (el >= 10.0 && stepSeconds == 1) {
                // AOS at 10 degrees threshold
                inPass = true;
                currentPass.satName = tle.name;
                currentPass.aosTime = t;
                currentPass.startAz = topo.az;
                currentPass.maxElevTime = t;
                currentPass.maxElevation = el;
                currentPass.maxAz = topo.az;
                currentPass.isVisible = false;
                currentPass.visibleDuration = 0;
            }
        } else {
            // We are in a pass (el >= 10.0 usually, but can fluctuate)
            // Update max elevation
            if (el > currentPass.maxElevation) {
                currentPass.maxElevation = el;
                currentPass.maxElevTime = t;
                currentPass.maxAz = topo.az;
            }
            
            // 3. Visibility Check
            SunPositionData sunPos = sunCalc.calculatePosition(t, _userLat, _userLon);
            bool isNight = (sunPos.altitude < -6.0);
            
            // Precise Earth Umbra Shadow Check
            GeodeticCoord satPos = CoordTransform::ecefToGeodetic(ecef);
            double latR = satPos.lat * DEG_TO_RAD;
            double lonR = satPos.lon * DEG_TO_RAD;
            double subLatR = sunPos.subsolarLat * DEG_TO_RAD;
            double subLonR = sunPos.subsolarLon * DEG_TO_RAD;
            
            double cos_theta = sin(subLatR)*sin(latR) + cos(subLatR)*cos(latR)*cos(lonR - subLonR);
            bool satIlluminated = true;
            if (cos_theta < 0) {
                // Angle between satellite and sun > 90 deg. Check conical shadow approximation.
                double earthRadius = 6378.137;
                double dist_sat = earthRadius + satPos.alt;
                double shadow_dist = dist_sat * sqrt(1.0 - cos_theta * cos_theta);
                if (shadow_dist < earthRadius) {
                    satIlluminated = false; // Eclipsed by Earth
                }
            }
            
            if (isNight && satIlluminated) {
                currentPass.isVisible = true;
                currentPass.visibleDuration += stepSeconds;
            }
            
            // LOS (Loss of Signal) threshold: drops below 10 degrees
            if (el < 10.0) {
                currentPass.losTime = t;
                currentPass.endAz = topo.az;
                inPass = false;
                
                if (currentPass.isVisible && currentPass.visibleDuration > 30) {
                    currentPass.score = calculateScore(currentPass.maxElevation, currentPass.visibleDuration, tle.baseScore);
                    passes.push_back(currentPass);
                }
            }
        }
        
        if (el < 0.0 && stepSeconds == 1 && !inPass) {
            // Satellite is below horizon and we are fine-stepping. Switch back to coarse step.
            stepSeconds = 60;
        }
        
        t += stepSeconds;
    }
    
    return passes;
}

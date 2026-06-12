#pragma once

#include <vector>
#include <Arduino.h>
#include "tle_data.h"
#include "coord_transform.h"

// Define a visible pass event
struct PassEvent {
    String satName;
    uint32_t aosTime;       // Acquisition of Signal (seconds since epoch)
    uint32_t losTime;       // Loss of Signal
    uint32_t maxElevTime;   // Time of Maximum Elevation
    
    float maxElevation;     // Maximum Elevation in degrees
    float maxBrightness;    // Estimated maximum brightness (magnitude, lower is brighter)
    
    float startAz;          // Azimuth at AOS in degrees
    float endAz;            // Azimuth at LOS in degrees
    float maxAz;            // Azimuth at Maximum Elevation in degrees
    
    bool isVisible;         // True if the pass is visually observable (in night + satellite illuminated)
    float visibleDuration;  // Duration of visibility in seconds
    
    int score;              // 1 to 5 stars
};

class ObservationPredictor {
public:
    ObservationPredictor(double userLat, double userLon, double userAlt);
    
    // Predict passes for a satellite over a given number of days starting from startTime
    std::vector<PassEvent> predictPasses(const TLEData& tle, uint32_t startTime, int daysToPredict);

private:
    double _userLat;
    double _userLon;
    double _userAlt;
    
    // Helper to calculate score based on max elevation and visible duration
    int calculateScore(float maxElevation, float visibleDuration, int baseScore);
};

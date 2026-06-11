#pragma once

struct GeoPoint {
    float lat;
    float lon;
};

// Extremely simplified continent outlines to save memory and CPU
const GeoPoint ASIA_POINTS[] = {
    {70, 60}, {70, 150}, {50, 140}, {30, 120}, {10, 110}, {0, 100}, 
    {-10, 120}, {-10, 100}, {10, 80}, {15, 40}, {30, 35}, {40, 50}, {60, 50}
};
const int ASIA_POINTS_COUNT = sizeof(ASIA_POINTS) / sizeof(GeoPoint);

const GeoPoint EUROPE_POINTS[] = {
    {70, 10}, {70, 40}, {50, 40}, {40, 30}, {35, 10}, {35, -10}, {50, -10}, {60, 0}
};
const int EUROPE_POINTS_COUNT = sizeof(EUROPE_POINTS) / sizeof(GeoPoint);

const GeoPoint AMERICA_POINTS[] = {
    {70, -160}, {70, -60}, {50, -60}, {30, -80}, {10, -80}, {10, -70}, {-10, -40}, 
    {-50, -70}, {-50, -80}, {0, -80}, {20, -105}, {50, -130}
};
const int AMERICA_POINTS_COUNT = sizeof(AMERICA_POINTS) / sizeof(GeoPoint);

const GeoPoint AFRICA_POINTS[] = {
    {35, -10}, {35, 30}, {15, 45}, {-35, 20}, {-35, 15}, {0, 10}, {10, -15}
};
const int AFRICA_POINTS_COUNT = sizeof(AFRICA_POINTS) / sizeof(GeoPoint);

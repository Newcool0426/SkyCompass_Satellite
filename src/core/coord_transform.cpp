#include "coord_transform.h"
#include <math.h>

const double WGS84_A = 6378.137;           // Semi-major axis in km
const double WGS84_E2 = 0.00669437999014;  // First eccentricity squared
const double PI_CONST = 3.14159265358979323846;

double CoordTransform::unixToJulian(uint32_t unix_ts) {
    return (unix_ts / 86400.0) + 2440587.5;
}

double CoordTransform::getGMST(double julian_date) {
    double T = (julian_date - 2451545.0) / 36525.0;
    double gmst_sec = 24110.54841 + 8640184.812866 * T + 0.093104 * T * T - 6.2e-6 * T * T * T;
    double gmst_rad = fmod(gmst_sec, 86400.0) * 2.0 * PI_CONST / 86400.0;
    if (gmst_rad < 0.0) {
        gmst_rad += 2.0 * PI_CONST;
    }
    return gmst_rad;
}

ECEFCoord CoordTransform::temeToECEF(double teme_x, double teme_y, double teme_z, double gmst) {
    ECEFCoord ecef;
    ecef.x = teme_x * cos(gmst) + teme_y * sin(gmst);
    ecef.y = teme_x * -sin(gmst) + teme_y * cos(gmst);
    ecef.z = teme_z;
    return ecef;
}

GeodeticCoord CoordTransform::ecefToGeodetic(const ECEFCoord& ecef) {
    GeodeticCoord geo;
    double r_delta = sqrt(ecef.x * ecef.x + ecef.y * ecef.y);
    double lon = atan2(ecef.y, ecef.x);
    
    // Iterative calculation for latitude and altitude
    double lat = atan2(ecef.z, r_delta * (1.0 - WGS84_E2));
    double N = WGS84_A;
    double alt = 0.0;
    
    for (int i = 0; i < 5; i++) {
        double sin_lat = sin(lat);
        N = WGS84_A / sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat);
        alt = r_delta / cos(lat) - N;
        lat = atan2(ecef.z, r_delta * (1.0 - WGS84_E2 * (N / (N + alt))));
    }
    
    geo.lat = lat * 180.0 / PI_CONST;
    geo.lon = lon * 180.0 / PI_CONST;
    geo.alt = alt;

    // Normalize longitude to -180 to 180
    while (geo.lon > 180.0) geo.lon -= 360.0;
    while (geo.lon < -180.0) geo.lon += 360.0;
    
    return geo;
}

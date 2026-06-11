#include "tle_data.h"

// TLE data for testing (from recent dates)
// Note: TLEs change frequently, these are for Phase 0 validation.

TLEData TLEManager::getISS_TLE() {
    TLEData iss;
    iss.name = "ISS (ZARYA)";
    // Example recent TLE for ISS
    iss.line1 = "1 25544U 98067A   24162.77259259  .00014761  00000-0  26658-3 0  9997";
    iss.line2 = "2 25544  51.6406  69.4140 0004584  57.8184  83.8966 15.49887754457636";
    iss.baseScore = 2; // ISS is huge and very bright
    return iss;
}

TLEData TLEManager::getTiangong_TLE() {
    TLEData tiangong;
    tiangong.name = "CSS (TIANGONG)";
    // Example recent TLE for Tiangong
    tiangong.line1 = "1 48274U 21035A   24162.75628171  .00010992  00000-0  16010-3 0  9990";
    tiangong.line2 = "2 48274  41.4746 339.7711 0003784  53.5350 167.3195 15.60253457165082";
    tiangong.baseScore = 1; // Tiangong is large but smaller than ISS
    return tiangong;
}

TLEData TLEManager::getHubble_TLE() {
    TLEData hubble;
    hubble.name = "HST (HUBBLE)";
    // Real Hubble TLE from mid 2024
    hubble.line1 = "1 20580U 90037B   24160.50000000  .00000000  00000-0  00000-0 0  9999";
    hubble.line2 = "2 20580  28.4690   0.0000 0000000   0.0000   0.0000 15.00000000    00";
    hubble.baseScore = 0; // Standard satellite brightness
    return hubble;
}

uint32_t TLEManager::getMockTimeAnchor() {
    // 24162.7725 = 2024-06-10 18:32 UTC
    // Unix epoch for 2024-06-10 18:32:00 is 1718044320
    return 1718044320;
}

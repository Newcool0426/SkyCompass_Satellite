import math

DEG_TO_RAD = math.pi / 180.0

def test():
    # 06-14 21:50 UTC (which is 06-15 05:50 UTC+8)
    unix_time = 1781473800 
    JD = unix_time / 86400.0 + 2440587.5
    T = (JD - 2451545.0) / 36525.0
    GMST_deg = (280.46061837 + 360.98564736629 * (JD - 2451545.0) + 0.000387933 * T * T) % 360.0
    if GMST_deg < 0: GMST_deg += 360.0
    GMST_rad = GMST_deg * DEG_TO_RAD
    
    print(f"GMST: {GMST_deg}")
    
    # Camera
    cLat = 66.90
    cLon = -51.60
    cLatRad = cLat * DEG_TO_RAD
    cLonRad = cLon * DEG_TO_RAD
    
    stars = [
        {"name": "Rigil Kentaurus", "ra": 219.9021, "dec": -60.8339},
        {"name": "Hadar", "ra": 210.9558, "dec": -60.3731},
        {"name": "Acrux", "ra": 186.6496, "dec": -63.0992},
        {"name": "Mimosa", "ra": 191.9300, "dec": -59.6886},
        {"name": "Gacrux", "ra": 187.7913, "dec": -57.1131},
    ]
    
    for star in stars:
        ra_rad = star['ra'] * DEG_TO_RAD
        dec_rad = star['dec'] * DEG_TO_RAD
        star_lon_rad = ra_rad - GMST_rad
        dLon = star_lon_rad - cLonRad
        
        cos_c = math.sin(cLatRad)*math.sin(dec_rad) + math.cos(cLatRad)*math.cos(dec_rad)*math.cos(dLon)
        
        print(f"{star['name']} cos_c: {cos_c}")
        if cos_c < 0:
            x = math.cos(dec_rad) * math.sin(dLon)
            y = math.cos(cLatRad)*math.sin(dec_rad) - math.sin(cLatRad)*math.cos(dec_rad)*math.cos(dLon)
            print(f"  Visible! x: {x:.2f}, y: {y:.2f}")

test()

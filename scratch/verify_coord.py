from skyfield.api import EarthSatellite, load, wgs84
from datetime import datetime, timezone

ts = load.timescale()
line1 = '1 25544U 98067A   26163.80312907  .00008495  00000+0  16106-3 0  9990'
line2 = '2 25544  51.6335 321.7912 0004900 178.5917 181.5086 15.49196054571074'
satellite = EarthSatellite(line1, line2, 'ISS (ZARYA)', ts)

dt = datetime(2026, 6, 15, 3, 48, 10, tzinfo=timezone.utc)
t = ts.from_datetime(dt)

geocentric = satellite.at(t)
subpoint = wgs84.subpoint(geocentric)

print('Latitude:', subpoint.latitude.degrees)
print('Longitude:', subpoint.longitude.degrees)
print('Elevation (km):', subpoint.elevation.km)

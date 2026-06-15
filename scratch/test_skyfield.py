from sgp4.api import Satrec, WGS84
from sgp4.api import jday
import numpy as np
from datetime import datetime, timedelta, timezone
import math

s = '1 25544U 98067A   26163.80312907  .00008495  00000+0  16106-3 0  9990'
t = '2 25544  51.6335 321.7912 0004900 178.5917 181.5086 15.49196054571074'
satellite = Satrec.twoline2rv(s, t)

# Lat Lon Alt of Nanning
lat_deg = 22.85
lon_deg = 108.33
alt_km = 0.109

# we need to transform ECI to topocentric
# But wait, python sgp4 returns TEME.
# To convert TEME to geodetic accurately requires skyfield. Let's install it.

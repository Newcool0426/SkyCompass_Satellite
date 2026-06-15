import ephem
from datetime import datetime, timedelta
import math

tles = {
    "ISS": ("1 25544U 98067A   26163.80312907  .00008495  00000+0  16106-3 0  9990", 
            "2 25544  51.6335 321.7912 0004900 178.5917 181.5086 15.49196054571074"),
    "Tiangong": ("1 48274U 21035A   26163.81770925  .00021976  00000+0  26094-3 0  9991", 
                 "2 48274  41.4694 348.5894 0007968  41.6006 318.5438 15.60618766292486"),
    "Hubble": ("1 20580U 90037B   26163.25344175  .00006001  00000+0  18892-3 0  9990", 
               "2 20580  28.4709 114.2921 0001952  91.9422 268.1398 15.30693075787818")
}

obs = ephem.Observer()
obs.lat = '22.85'
obs.lon = '108.33'
obs.elevation = 109

start_date = datetime(2026, 6, 12, 0, 0, 0)
end_date = start_date + timedelta(days=10)

for name, (l1, l2) in tles.items():
    print(f"\n--- {name} ---")
    sat = ephem.readtle(name, l1, l2)
    t = start_date
    obs.date = t
    
    while obs.date.datetime() < end_date:
        try:
            info = obs.next_pass(sat)
            trise, azrise, tmax, altmax, tset, azset = info
            
            # Print if max elevation is > 10 degrees
            if math.degrees(altmax) > 10:
                print(f"Pass Date: {tmax.datetime().strftime('%Y-%m-%d')}")
                print(f"Start: {trise.datetime().strftime('%H:%M:%S')} (el: 0)")
                print(f"Max: {tmax.datetime().strftime('%H:%M:%S')} (el: {math.degrees(altmax):.1f})")
                print(f"End: {tset.datetime().strftime('%H:%M:%S')} (el: 0)\n")
            
            obs.date = tset + ephem.minute * 5
        except ValueError:
            obs.date = obs.date + ephem.hour * 1

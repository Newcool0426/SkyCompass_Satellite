import urllib.request
import json

url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=json"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    
    for sat in data:
        name = sat['OBJECT_NAME']
        if 'FALCON 9' in name or 'CENTAUR' in name or 'DELTA' in name or 'ARIANE' in name:
            if 'R/B' in name:
                print(f"{sat['NORAD_CAT_ID']}: {name}")

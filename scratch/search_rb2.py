import urllib.request
import json

url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    
    for sat in data:
        name = sat['OBJECT_NAME']
        if 'FALCON' in name and 'R/B' in name:
            print(f"{sat['NORAD_CAT_ID']}: {name}")
            break # Just need one

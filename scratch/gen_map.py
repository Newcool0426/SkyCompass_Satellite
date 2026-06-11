import urllib.request
import json
import ssl

url = "https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_110m_land.geojson"
print("Fetching map data...")
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

polygons = []
for feature in data['features']:
    geom = feature['geometry']
    if geom['type'] == 'Polygon':
        polygons.append(geom['coordinates'][0])
    elif geom['type'] == 'MultiPolygon':
        for poly in geom['coordinates']:
            polygons.append(poly[0])

total_points = sum(len(p) for p in polygons)
print(f"Total points: {total_points}")

cpp_code = "#ifndef EARTH_DATA_H\n#define EARTH_DATA_H\n\n"
cpp_code += "struct MapPath { int length; const float* points; };\n\n"

valid_polys = []
for i, poly in enumerate(polygons):
    if len(poly) < 10: continue # Skip very small islands
    
    # Downsample: take every 4th point, but ensure start and end are kept to close the shape
    simplified = poly[::4]
    if simplified[-1] != poly[-1]:
        simplified.append(poly[-1])
        
    valid_polys.append((i, simplified))

total_valid_points = sum(len(p) for _, p in valid_polys)
print(f"Total points after downsampling: {total_valid_points}")

for i, poly in valid_polys:
    cpp_code += f"const float map_path_{i}[] = {{\n    "
    pts = []
    for pt in poly:
        lon, lat = pt
        pts.append(f"{lat:.2f}f, {lon:.2f}f")
    cpp_code += ", ".join(pts)
    cpp_code += "\n};\n"

cpp_code += f"\nconst MapPath world_map[] = {{\n"
for i, poly in valid_polys:
    cpp_code += f"    {{{len(poly)}, map_path_{i}}},\n"
cpp_code += "};\n"
cpp_code += f"const int world_map_count = {len(valid_polys)};\n\n"
cpp_code += "#endif\n"

with open("d:/workspace/SkyCompass_Satellite/src/core/earth_data.h", "w", encoding="utf-8") as f:
    f.write(cpp_code)
print("earth_data.h generated successfully!")

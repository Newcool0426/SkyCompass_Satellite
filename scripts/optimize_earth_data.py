import os
import re
import math

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    header_path = os.path.join(script_dir, "..", "src", "core", "earth_data.h")
    
    if not os.path.exists(header_path):
        print(f"Error: {header_path} not found.")
        return

    with open(header_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all path arrays
    # e.g., const float map_path_0[] = { ... };
    path_pattern = re.compile(r'const\s+float\s+(map_path_\d+)\s*\[\s*\]\s*=\s*\{([^{}]+)\}\s*;', re.DOTALL)
    paths = path_pattern.findall(content)
    
    print(f"Found {len(paths)} map paths.")

    # Let's parse world_map array
    world_map_pattern = re.compile(r'const\s+MapPath\s+world_map\s*\[\s*\]\s*=\s*\{(.*?)\}\s*;', re.DOTALL)
    world_map_match = world_map_pattern.search(content)
    if not world_map_match:
        print("Error: world_map array not found.")
        return
        
    world_map_content = world_map_match.group(1).strip()
    
    # Generate new header content
    new_content = []
    new_content.append("#ifndef EARTH_DATA_H")
    new_content.append("#define EARTH_DATA_H")
    new_content.append("")
    new_content.append("struct MapPoint {")
    new_content.append("    float sinLat;")
    new_content.append("    float cosLat;")
    new_content.append("    float sinLon;")
    new_content.append("    float cosLon;")
    new_content.append("    float latRad;")
    new_content.append("};")
    new_content.append("")
    new_content.append("struct MapPath { int length; const MapPoint* points; };")
    new_content.append("")

    for name, pts_str in paths:
        # Extract floats
        # Remove comments or whitespace
        cleaned = pts_str.replace('\n', ' ').replace('\r', ' ')
        float_strs = re.findall(r'[-+]?\d*\.\d+|\b[-+]?\d+\b', cleaned)
        floats = []
        for s in float_strs:
            try:
                floats.append(float(s))
            except ValueError:
                pass
        
        # Verify coordinates are in pairs (lat, lon)
        if len(floats) % 2 != 0:
            print(f"Warning: Odd number of coordinates in {name}")
            
        new_content.append(f"const MapPoint {name}[] = {{")
        points_lines = []
        for idx in range(0, len(floats), 2):
            lat = floats[idx]
            lon = floats[idx+1]
            lat_rad = math.radians(lat)
            lon_rad = math.radians(lon)
            sin_lat = math.sin(lat_rad)
            cos_lat = math.cos(lat_rad)
            sin_lon = math.sin(lon_rad)
            cos_lon = math.cos(lon_rad)
            points_lines.append(f"    {{{sin_lat:.6f}f, {cos_lat:.6f}f, {sin_lon:.6f}f, {cos_lon:.6f}f, {lat_rad:.6f}f}}")
        
        new_content.append(",\n".join(points_lines))
        new_content.append("};")
        new_content.append("")

    # Output the world_map array
    new_content.append("const MapPath world_map[] = {")
    
    # Parse individual entries in world_map_content
    # e.g., {4, map_path_0},
    entries = re.findall(r'\{\s*(\d+)\s*,\s*(map_path_\d+)\s*\}', world_map_content)
    entry_lines = []
    for length, name in entries:
        entry_lines.append(f"    {{{length}, {name}}}")
        
    new_content.append(",\n".join(entry_lines))
    new_content.append("};")
    new_content.append("")
    
    # Count of elements
    new_content.append(f"const int world_map_count = {len(entries)};")
    new_content.append("")
    new_content.append("#endif")
    new_content.append("")

    with open(header_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_content))
        
    print(f"Successfully optimized {header_path}")

if __name__ == "__main__":
    main()

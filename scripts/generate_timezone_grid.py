import sys
import os

try:
    from timezonefinder import TimezoneFinder
    import pytz
    from datetime import datetime
except ImportError:
    print("Installing required packages: timezonefinder, pytz")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "timezonefinder", "pytz"])
    from timezonefinder import TimezoneFinder
    import pytz
    from datetime import datetime

def generate_grid():
    tf = TimezoneFinder()
    dt = datetime(2026, 1, 1)  # Use a standard winter date to get standard time (avoid DST)
    
    grid = []
    
    # 180 rows (latitude 89 to -90)
    # 360 cols (longitude -180 to 179)
    for lat in range(89, -91, -1):
        row = []
        for lon in range(-180, 180, 1):
            # Center of the cell
            lat_center = lat + 0.5
            lon_center = lon + 0.5
            
            tz_name = tf.timezone_at(lng=lon_center, lat=lat_center)
            if tz_name:
                try:
                    tz = pytz.timezone(tz_name)
                    # Get offset in seconds, convert to hours
                    offset = tz.utcoffset(dt).total_seconds() / 3600.0
                    row.append(int(round(offset)))
                except Exception:
                    # Fallback to nautical timezone
                    row.append(int(round(lon_center / 15.0)))
            else:
                # Fallback to nautical timezone
                row.append(int(round(lon_center / 15.0)))
        grid.append(row)
        if lat % 30 == 0:
            print(f"Processed latitude {lat}...")

    # Write to C header file
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "core", "timezone_grid.h")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("#ifndef TIMEZONE_GRID_H\n")
        f.write("#define TIMEZONE_GRID_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("// Auto-generated offline timezone grid map (1x1 degree)\n")
        f.write("// Rows (180): Latitude 89 to -90\n")
        f.write("// Cols (360): Longitude -180 to 179\n")
        f.write("const int8_t timezone_map[180][360] = {\n")
        
        for i, row in enumerate(grid):
            f.write("    {")
            f.write(", ".join(map(str, row)))
            f.write("}")
            if i < len(grid) - 1:
                f.write(",\n")
            else:
                f.write("\n")
        
        f.write("};\n\n")
        f.write("#endif // TIMEZONE_GRID_H\n")
        
    print(f"Successfully generated timezone grid at: {output_path}")

if __name__ == "__main__":
    generate_grid()

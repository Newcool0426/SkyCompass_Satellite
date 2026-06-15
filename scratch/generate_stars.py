import urllib.request
import csv

# We will just write the C++ code directly for the 30 brightest stars
stars = [
    ("Sirius", "06h 45m 08.9s", "-16d 42m 58s", -1.46, "TFT_WHITE"),
    ("Canopus", "06h 23m 57.1s", "-52d 41m 44s", -0.74, "TFT_WHITE"),
    ("Rigil Kentaurus", "14h 39m 36.5s", "-60d 50m 02s", -0.27, "TFT_YELLOW"),
    ("Arcturus", "14h 15m 39.7s", "+19d 10m 56s", -0.05, "TFT_ORANGE"),
    ("Vega", "18h 36m 56.3s", "+38d 47m 01s", 0.03, "TFT_WHITE"),
    ("Capella", "05h 16m 41.4s", "+45d 59m 53s", 0.08, "TFT_YELLOW"),
    ("Rigel", "05h 14m 32.3s", "-08d 12m 06s", 0.13, "TFT_CYAN"),
    ("Procyon", "07h 39m 18.1s", "+05d 13m 30s", 0.34, "TFT_WHITE"),
    ("Achernar", "01h 37m 42.8s", "-57d 14m 12s", 0.46, "TFT_CYAN"),
    ("Betelgeuse", "05h 55m 10.3s", "+07d 24m 25s", 0.50, "TFT_RED"),
    ("Hadar", "14h 03m 49.4s", "-60d 22m 23s", 0.61, "TFT_CYAN"),
    ("Altair", "19h 50m 47.0s", "+08d 52m 06s", 0.76, "TFT_WHITE"),
    ("Acrux", "12h 26m 35.9s", "-63d 05m 57s", 0.76, "TFT_CYAN"),
    ("Aldebaran", "04h 35m 55.2s", "+16d 30m 33s", 0.86, "TFT_ORANGE"),
    ("Antares", "16h 29m 24.4s", "-26d 25m 55s", 0.96, "TFT_RED"),
    ("Spica", "13h 25m 11.6s", "-11d 09m 41s", 0.97, "TFT_CYAN"),
    ("Pollux", "07h 45m 18.9s", "+28d 01m 34s", 1.14, "TFT_ORANGE"),
    ("Fomalhaut", "22h 57m 39.0s", "-29d 37m 20s", 1.16, "TFT_WHITE"),
    ("Deneb", "20h 41m 25.9s", "+45d 16m 49s", 1.25, "TFT_WHITE"),
    ("Mimosa", "12h 47m 43.2s", "-59d 41m 19s", 1.25, "TFT_CYAN"),
    ("Regulus", "10h 08m 22.3s", "+11d 58m 02s", 1.35, "TFT_CYAN"),
    ("Adhara", "12h 15m 08.7s", "-58d 44m 56s", 1.50, "TFT_CYAN"),
    ("Castor", "07h 34m 36.0s", "+31d 53m 18s", 1.58, "TFT_WHITE"),
    ("Gacrux", "12h 31m 09.9s", "-57d 06m 47s", 1.63, "TFT_RED"),
    ("Shaula", "17h 33m 36.5s", "-37d 06m 13s", 1.62, "TFT_CYAN")
]

def parse_ra(ra):
    h, m, s = ra.replace('h', '').replace('m', '').replace('s', '').split()
    return (float(h) + float(m)/60 + float(s)/3600) * 15.0

def parse_dec(dec):
    d, m, s = dec.replace('d', '').replace('m', '').replace('s', '').split()
    sign = -1 if d.startswith('-') else 1
    return sign * (abs(float(d)) + float(m)/60 + float(s)/3600)

cpp_code = "struct BrightStar {\n    const char* name;\n    float ra;\n    float dec;\n    float mag;\n    uint16_t color;\n};\n\n"
cpp_code += "const BrightStar BRIGHT_STARS[] = {\n"
for name, ra, dec, mag, color in stars:
    ra_deg = parse_ra(ra)
    dec_deg = parse_dec(dec)
    cpp_code += f'    {{"{name}", {ra_deg:.4f}f, {dec_deg:.4f}f, {mag}f, {color}}},\n'
cpp_code += "};\n"
cpp_code += f"const int NUM_BRIGHT_STARS = {len(stars)};\n"

print(cpp_code)

import csv
import io
from pathlib import Path
from urllib.request import Request, urlopen

URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/monthly/data/N_09_extent_v4.0.csv"
)
OUTPUT = Path("data/arctic_sea_ice/september_extent.csv")

request = Request(URL, headers={"User-Agent": "Earth-Health-data-downloader/1.0"})
with urlopen(request, timeout=30) as response:
    raw = response.read()

text = raw.decode("utf-8-sig")
rows = list(csv.reader(io.StringIO(text)))
years = [
    int(row[0].strip())
    for row in rows
    if row and row[0].strip().isdigit()
]

if len(years) < 20 or len(years) != len(set(years)):
    raise ValueError("Stažený soubor nevypadá jako platná roční řada NSIDC.")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if not OUTPUT.exists() or OUTPUT.read_bytes() != raw:
    OUTPUT.write_bytes(raw)
    print(f"Uloženo {len(years)} ročních záznamů: {OUTPUT}")
else:
    print("Zářijová data arktického ledu se nezměnila.")
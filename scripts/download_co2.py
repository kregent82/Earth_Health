import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_gl.csv"
OUTPUT = Path("data/co2_global")

request = Request(URL, headers={"User-Agent": "Earth-Health-data-downloader/1.0"})
with urlopen(request, timeout=30) as response:
    raw = response.read()

text = raw.decode("utf-8-sig")
rows = csv.reader(
    line for line in io.StringIO(text)
    if line.strip() and not line.lstrip().startswith("#")
)

years = []
for row in rows:
    if row and row[0].strip().isdigit():
        year = int(row[0].strip())
        if len(row) < 2 or not row[1].strip():
            raise ValueError(f"Chybí hodnota CO₂ pro rok {year}")
        float(row[1].strip())
        years.append(year)

if len(years) < 20 or 2025 not in years or len(years) != len(set(years)):
    raise ValueError("CSV neobsahuje očekávanou roční řadu včetně roku 2025.")

OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT / "co2_annmean_gl.csv").write_bytes(raw)

metadata = {
    "source_url": URL,
    "downloaded_utc": datetime.now(timezone.utc).isoformat(),
    "source_sha256": hashlib.sha256(raw).hexdigest(),
    "first_year": min(years),
    "last_year_in_source": max(years),
    "unit": "ppm",
    "metric": "Roční globální průměr koncentrace CO₂",
}
(OUTPUT / "metadata.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"CO₂: staženo {len(years)} ročních záznamů.")
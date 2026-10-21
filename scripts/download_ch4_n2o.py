import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://gml.noaa.gov/aggi/NOAA_Annual_Mean_MoleFractions.csv"
DATASETS = {
    "CH4": Path("data/ch4_global"),
    "N2O": Path("data/n2o_global"),
}

request = Request(URL, headers={"User-Agent": "Earth-Health-data-downloader/1.0"})
with urlopen(request, timeout=30) as response:
    raw = response.read()

rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
header_index = next(
    (i for i, row in enumerate(rows)
     if len(row) >= 4 and row[1:4] == ["CO2", "CH4", "N2O"]),
    None,
)
if header_index is None:
    raise ValueError("Ve zdrojovém CSV chybí očekávaná záhlaví CO2, CH4, N2O.")

header = rows[header_index]
units = rows[header_index + 1]
indexes = {gas: header.index(gas) for gas in DATASETS}
if any(units[index] != "ppb" for index in indexes.values()):
    raise ValueError("Změnily se očekávané jednotky CH4 nebo N2O.")

series = {gas: [] for gas in DATASETS}
years = []

for row in rows[header_index + 2:]:
    if not row:
        continue
    try:
        year_label = float(row[0])
    except (ValueError, IndexError):
        continue  # Textové poznámky a citace pod tabulkou

    year = int(year_label)
    if year_label != year + 0.5 or not 1970 <= year <= datetime.now().year:
        raise ValueError(f"Neočekávané označení roku: {row[0]!r}")
    if year in years:
        raise ValueError(f"Duplicitní rok: {year}")

    for gas, index in indexes.items():
        value = float(row[index])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"Neplatná hodnota {gas} pro rok {year}")
        series[gas].append((year, value))
    years.append(year)

if not years or years != sorted(years) or max(years) < 2024:
    raise ValueError("Roční řada je prázdná, neuspořádaná nebo příliš stará.")

digest = hashlib.sha256(raw).hexdigest()
downloaded = datetime.now(timezone.utc).isoformat()

for gas, folder in DATASETS.items():
    folder.mkdir(parents=True, exist_ok=True)
    source_file = folder / "source.csv"
    output_file = folder / "annual.csv"
    metadata_file = folder / "metadata.json"

    # Beze změny zdroje nevytvářejte nový commit jen kvůli času stažení.
    if (source_file.exists() and source_file.read_bytes() == raw
            and output_file.exists() and metadata_file.exists()):
        print(f"{gas}: zdroj se nezměnil.")
        continue

    source_file.write_bytes(raw)
    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["year", "concentration_ppb"])
        writer.writerows(series[gas])

    metadata_file.write_text(
        json.dumps(
            {
                "source_url": URL,
                "downloaded_utc": downloaded,
                "source_sha256": digest,
                "metric": gas,
                "unit": "ppb",
                "first_year": min(years),
                "last_year": max(years),
                "note": "Roční globální povrchový průměr NOAA pro podklady AGGI.",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"{gas}: uloženo {len(series[gas])} ročních hodnot.")
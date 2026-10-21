import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

INDICATORS = {
    "SH.DYN.MORT": ("under5_mortality", 1990, 2024, "úmrtí na 1 000 živě narozených"),
    "SH.H2O.SMDW.ZS": ("safe_drinking_water", 2000, 2024, "% populace"),
}

for code, (folder_name, first, last, unit) in INDICATORS.items():
    url = (
        f"https://api.worldbank.org/v2/country/1W/indicator/{code}"
        "?format=json&per_page=200"
    )
    request = Request(url, headers={"User-Agent": "Earth-Health/1.0"})
    with urlopen(request, timeout=45) as response:
        raw = response.read()

    payload = json.loads(raw)
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError(f"{code}: neočekávaná odpověď API")
    info, records = payload

    values = {}
    for row in records:
        if row["indicator"]["id"] != code or row["country"]["id"] != "1W":
            raise ValueError(f"{code}: jiný ukazatel nebo území")
        year = int(row["date"])
        if first <= year <= last and row["value"] is not None:
            if year in values:
                raise ValueError(f"{code}: duplicitní rok {year}")
            value = float(row["value"])
            if value < 0 or (unit == "% populace" and value > 100):
                raise ValueError(f"{code}: neplatná hodnota {year}")
            values[year] = value

    expected = set(range(first, last + 1))
    if set(values) != expected:
        raise ValueError(f"{code}: chybějí roky {sorted(expected - set(values))}")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["year", "value"])
    writer.writerows((year, values[year]) for year in sorted(values))

    folder = Path("data") / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / "source.json"
    if source.exists() and source.read_bytes() == raw:
        print(f"{code}: zdroj beze změny")
        continue

    source.write_bytes(raw)
    (folder / "annual.csv").write_text(output.getvalue(), encoding="utf-8")
    (folder / "metadata.json").write_text(
        json.dumps({
            "source_url": url,
            "publisher_of_download": "World Bank API",
            "indicator": code,
            "unit": unit,
            "api_last_updated": info.get("lastupdated"),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "limitation": (
                "Bez intervalů nejistoty z portálu UN IGME"
                if code == "SH.DYN.MORT" else
                "Agregát API Světové banky; ověřit proti vydání JMP"
            ),
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
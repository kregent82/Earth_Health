import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

URL = (
    "https://www.metoffice.gov.uk/hadobs/hadcrut5/data/"
    "HadCRUT.5.2.0.0/analysis/diagnostics/"
    "HadCRUT.5.2.0.0.analysis.summary_series.global.annual.csv"
)
OUT = Path("data/hadcrut5")
OUT.mkdir(parents=True, exist_ok=True)

with urlopen(URL, timeout=60) as response:
    raw = response.read()

text = raw.decode("utf-8-sig")
rows = list(csv.DictReader(io.StringIO(text)))
required = {
    "Time",
    "Anomaly (deg C)",
    "Lower confidence limit (2.5%)",
    "Upper confidence limit (97.5%)",
}
if not rows or not required.issubset(rows[0]):
    raise ValueError("Neznámý nebo prázdný formát CSV; data neukládám.")

complete = []
for row in rows:
    year = int(row["Time"])
    if year <= 2025:
        for column in required - {"Time"}:
            float(row[column])
        complete.append(row)

if not complete or int(complete[-1]["Time"]) != 2025:
    raise ValueError("Chybí očekávaný rok 2025; data neukládám.")

(OUT / "source.csv").write_bytes(raw)
with (OUT / "annual_to_2025.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(complete)

metadata = {
    "source_url": URL,
    "version": "HadCRUT.5.2.0.0",
    "downloaded_utc": datetime.now(timezone.utc).isoformat(),
    "source_sha256": hashlib.sha256(raw).hexdigest(),
    "first_year": int(complete[0]["Time"]),
    "last_year": int(complete[-1]["Time"]),
    "method": "pozorování a statistická analýza",
    "reference_period": "1961–1990",
    "note": "Roční hodnota 2026 je z odvozeného souboru vyloučena.",
}
(OUT / "metadata.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
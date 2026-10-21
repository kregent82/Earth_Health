from pathlib import Path
from urllib.request import Request, urlopen

URL = (
    "https://www.ncei.noaa.gov/data/oceans/woa/"
    "DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/"
    "h22-w0-2000m.dat"
)
DEST = Path("data/ocean_heat_0_2000m/source.dat")

request = Request(URL, headers={"User-Agent": "Earth-Health/1.0"})
with urlopen(request, timeout=45) as response:
    raw = response.read()

text = raw.decode("ascii")
years = []
for line in text.splitlines()[1:]:
    if not line.strip():
        continue
    try:
        year_marker = float(line[:8].strip())
    except ValueError as exc:
        raise ValueError("Neočekávaný formát ročního souboru NOAA") from exc
    year = int(year_marker)
    if year_marker != year + 0.5:
        raise ValueError(f"Neočekávaný údaj roku: {year_marker}")
    years.append(year)

print(
    f"NOAA: počet={len(years)}, "
    f"první={min(years) if years else 'žádný'}, "
    f"poslední={max(years) if years else 'žádný'}, "
    f"duplicity={len(years) - len(set(years))}"
)
print(f"Posledních 10 načtených roků: {years[-10:]}")

if (
    not years
    or years[0] != 2005
    or years[-1] < 2025
    or years != list(range(2005, years[-1] + 1))
):
    raise ValueError(
        "Roční soubor NOAA neobsahuje souvislou řadu od 2005 "
        "alespoň do 2025 v očekávaném pořadí."
    )

DEST.parent.mkdir(parents=True, exist_ok=True)
if not DEST.exists() or DEST.read_bytes() != raw:
    DEST.write_bytes(raw)
print(f"Obsah tepla v oceánu: {len(years)} ročních záznamů.")
"""
Extract Latin American births data from UN WPP 2024 and compute first decline years.
Source: UN World Population Prospects 2024, Demographic Indicators (Medium variant)
"""
import csv
import math

# Latin American countries with their UN M49 codes and ISO3 codes
COUNTRIES = {
    32: ("Argentina", "ARG"),
    68: ("Bolivia", "BOL"),
    76: ("Brazil", "BRA"),
    152: ("Chile", "CHL"),
    170: ("Colombia", "COL"),
    188: ("Costa Rica", "CRI"),
    192: ("Cuba", "CUB"),
    214: ("Dominican Republic", "DOM"),
    218: ("Ecuador", "ECU"),
    222: ("El Salvador", "SLV"),
    320: ("Guatemala", "GTM"),
    332: ("Haiti", "HTI"),
    340: ("Honduras", "HND"),
    484: ("Mexico", "MEX"),
    558: ("Nicaragua", "NIC"),
    591: ("Panama", "PAN"),
    600: ("Paraguay", "PRY"),
    604: ("Peru", "PER"),
    858: ("Uruguay", "URY"),
    862: ("Venezuela", "VEN"),
}

COUNTRY_IDS = set(COUNTRIES.keys())

INPUT_FILE = "WPP2024_Demographic_Indicators_Medium.csv"

# WPP2024 estimates go through 2024; projections start at 2025.
# Include up to 2024 for the births CSV output.
# For the decline analysis, use data through 2024 (historical only).
MAX_YEAR = 2024

# Step 1: Read the CSV and extract births data for Latin American countries
print("Reading WPP2024 demographic indicators...")
births_data = []  # list of (country, iso3, year, births)

with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        loc_id_str = row.get("LocID", "").strip()
        if not loc_id_str:
            continue
        try:
            loc_id = int(loc_id_str)
        except ValueError:
            continue
        if loc_id not in COUNTRY_IDS:
            continue

        year_str = row.get("Time", "").strip()
        births_str = row.get("Births", "").strip()
        variant = row.get("Variant", "").strip()

        if not year_str or not births_str:
            continue

        try:
            year = int(year_str)
        except ValueError:
            continue

        # Only include up to MAX_YEAR (historical estimates)
        if year > MAX_YEAR:
            continue

        # Only include Medium variant (estimates + medium projections)
        if variant != "Medium":
            continue

        try:
            births_thousands = float(births_str)
        except ValueError:
            continue

        country_name, iso3 = COUNTRIES[loc_id]
        # Convert from thousands to actual count, rounded to nearest integer
        births = round(births_thousands * 1000)

        births_data.append((country_name, iso3, year, births))

# Sort by country name, then year
births_data.sort(key=lambda x: (x[0], x[2]))

print(f"Found {len(births_data)} data points for {len(set(r[0] for r in births_data))} countries")

# Show year range per country
countries_seen = {}
for country, iso3, year, births in births_data:
    if country not in countries_seen:
        countries_seen[country] = {"min_year": year, "max_year": year, "count": 0}
    countries_seen[country]["min_year"] = min(countries_seen[country]["min_year"], year)
    countries_seen[country]["max_year"] = max(countries_seen[country]["max_year"], year)
    countries_seen[country]["count"] += 1

for c in sorted(countries_seen.keys()):
    info = countries_seen[c]
    print(f"  {c}: {info['min_year']}-{info['max_year']} ({info['count']} years)")

# Step 2: Write latam_births.csv
print("\nWriting latam_births.csv...")
with open("latam_births.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["country", "iso3", "year", "births"])
    for country, iso3, year, births in births_data:
        writer.writerow([country, iso3, year, births])

print(f"Wrote {len(births_data)} rows to latam_births.csv")

# Step 3: Compute first decline year (after all-time peak)
print("\nComputing first decline years...")

# Group by country
country_births = {}
for country, iso3, year, births in births_data:
    if country not in country_births:
        country_births[country] = {"iso3": iso3, "years": []}
    country_births[country]["years"].append((year, births))

# Sort each country's data by year
for country in country_births:
    country_births[country]["years"].sort()

decline_rows = []

for country in sorted(country_births.keys()):
    iso3 = country_births[country]["iso3"]
    years = country_births[country]["years"]

    # Find the all-time peak in births
    peak_births = 0
    peak_year = None
    for year, births in years:
        if births > peak_births:
            peak_births = births
            peak_year = year

    # Find the first year AFTER the peak where births declined from the previous year
    found = False
    for i in range(1, len(years)):
        year, births = years[i]
        prev_year, prev_births = years[i - 1]

        # Only look at years after (or at) the peak
        if prev_year < peak_year:
            continue

        if births < prev_births:
            pct_change = ((births - prev_births) / prev_births) * 100
            decline_rows.append({
                "country": country,
                "iso3": iso3,
                "first_decline_year": year,
                "prior_year_births": prev_births,
                "decline_year_births": births,
                "pct_change": round(pct_change, 1),
            })
            found = True
            break

    if not found:
        print(f"  WARNING: No decline found after peak for {country} (peak in {peak_year})")
    else:
        r = decline_rows[-1]
        print(f"  {country}: peak in {peak_year} ({peak_births:,}), first decline in {r['first_decline_year']} ({r['pct_change']}%)")

# Sort by first_decline_year ascending
decline_rows.sort(key=lambda x: x["first_decline_year"])

# Step 4: Write latam_first_decline.csv
print("\nWriting latam_first_decline.csv...")
with open("latam_first_decline.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["country", "iso3", "first_decline_year", "prior_year_births", "decline_year_births", "pct_change"])
    for row in decline_rows:
        writer.writerow([
            row["country"],
            row["iso3"],
            row["first_decline_year"],
            row["prior_year_births"],
            row["decline_year_births"],
            row["pct_change"],
        ])

print(f"Wrote {len(decline_rows)} rows to latam_first_decline.csv")
print("\nDone!")

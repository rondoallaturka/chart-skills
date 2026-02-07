#!/usr/bin/env python3
"""
Pull median household income and bachelor's degree attainment by
detailed Hispanic origin group from the Census Bureau API (ACS 1-Year S0201).

Usage:
    pip install requests
    python pull_hispanic_data.py

Outputs:
    - hispanic_scatter_data.json  (chart-ready for branded-charts scatter)
    - hispanic_raw_data.csv       (full data for inspection)

Data source: Census Bureau ACS 1-Year, Table S0201 (Selected Population Profile)
Tries 2024 first, falls back to 2023, then 2022.

Variables used:
    S0201_214E  = Median household income (dollars)
    S0201_099E  = % bachelor's degree or higher (population 25+)
"""

import requests
import json
import csv
import sys

# --- Configuration ---

# Hispanic origin group codes for S0201 (popgroup parameter)
# These codes correspond to the "Selected Population" filter on data.census.gov
ORIGIN_GROUPS = {
    "400": "Hispanic or Latino (of any race)",
    "4015": "Mexican",
    "4038": "Puerto Rican",
    "4036": "Cuban",
    "4037": "Dominican",
    "4017": "Costa Rican",
    "4018": "Guatemalan",
    "4019": "Honduran",
    "4020": "Nicaraguan",
    "4021": "Panamanian",
    "4022": "Salvadoran",
    "4025": "Argentinean",
    "4027": "Chilean",
    "4028": "Colombian",
    "4029": "Ecuadorian",
    "4031": "Peruvian",
    "4033": "Venezuelan",
    "4041": "Spaniard",
}

# ACS variables (S0201 = Selected Population Profile)
# Check variable names for your target year at:
# https://api.census.gov/data/{year}/acs/acs1/spp/variables.html
#
# These variable names can shift between ACS years. The script tries
# a few known variants automatically. If none work, inspect the
# variables endpoint above and update VARIABLE_CANDIDATES below.
VARIABLE_CANDIDATES = {
    "income": [
        "S0201_214E",   # Median household income (dollars)
        "S0201_127E",   # Alternate (older years)
        "S0201_126E",   # Alternate
    ],
    "bachelors": [
        "S0201_099E",   # Bachelor's degree or higher (%)
        "S0201_070E",   # Alternate (older years)
        "S0201_069E",   # Alternate
    ],
}

YEARS_TO_TRY = [2024, 2023, 2022]

BASE_URL = "https://api.census.gov/data/{year}/acs/acs1/spp"

# No API key needed for small queries, but you can add one here for reliability:
# API_KEY = "YOUR_KEY_HERE"  # Get free at https://api.census.gov/data/key_signup.html
API_KEY = None


def try_fetch(year, income_var, bach_var, group_code):
    """Attempt to fetch data for one group from the Census API."""
    params = {
        "get": f"NAME,{income_var},{bach_var}",
        "for": "us:1",
        "POPGROUP": group_code,
    }
    if API_KEY:
        params["key"] = API_KEY

    url = BASE_URL.format(year=year)
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1:
                return data
    except Exception:
        pass
    return None


def detect_working_variables(year):
    """Try variable combinations on a known large group (All Hispanics = 400)."""
    for inc_var in VARIABLE_CANDIDATES["income"]:
        for bach_var in VARIABLE_CANDIDATES["bachelors"]:
            result = try_fetch(year, inc_var, bach_var, "400")
            if result:
                header = result[0]
                row = result[1]
                # Verify we got numeric-ish values
                try:
                    inc_val = float(row[1]) if row[1] not in (None, "", "-", "N", "(X)") else None
                    bach_val = float(row[2]) if row[2] not in (None, "", "-", "N", "(X)") else None
                    if inc_val and bach_val:
                        return year, inc_var, bach_var
                except (ValueError, IndexError):
                    continue
    return None, None, None


def main():
    print("=" * 60)
    print("Census ACS: Hispanic Origin Income & Education Scatter Data")
    print("=" * 60)

    # Step 1: Find a working year + variable combo
    working_year = None
    inc_var = None
    bach_var = None

    for year in YEARS_TO_TRY:
        print(f"\nTrying ACS {year}...")
        working_year, inc_var, bach_var = detect_working_variables(year)
        if working_year:
            print(f"  ✓ Found working config: year={working_year}, "
                  f"income={inc_var}, bachelors={bach_var}")
            break
        else:
            print(f"  ✗ No valid response for {year}")

    if not working_year:
        print("\n❌ Could not find working variable combination.")
        print("   The variable names may have changed. Check:")
        print(f"   https://api.census.gov/data/2023/acs/acs1/subject/variables.html")
        print("   Look for variables related to 'median household income' and")
        print("   'bachelor's degree or higher' in the S0201 table.")
        sys.exit(1)

    # Step 2: Pull data for all origin groups
    print(f"\nPulling data for {len(ORIGIN_GROUPS)} origin groups...\n")

    results = []
    for code, label in ORIGIN_GROUPS.items():
        data = try_fetch(working_year, inc_var, bach_var, code)
        if data and len(data) > 1:
            row = data[1]
            try:
                income = float(row[1]) if row[1] not in (None, "", "-", "N", "(X)") else None
                bachelors = float(row[2]) if row[2] not in (None, "", "-", "N", "(X)") else None
            except (ValueError, IndexError):
                income, bachelors = None, None

            results.append({
                "code": code,
                "label": label,
                "short_label": label.replace(" or Latino (of any race)", ""),
                "median_household_income": income,
                "bachelors_pct": bachelors,
            })
            status = "✓" if (income and bachelors) else "⚠ partial"
            print(f"  {status} {label}: income=${income}, bachelors={bachelors}%")
        else:
            print(f"  ✗ {label}: no data returned")
            results.append({
                "code": code,
                "label": label,
                "short_label": label,
                "median_household_income": None,
                "bachelors_pct": None,
            })

    # Step 3: Build chart-ready scatter JSON (excluding "All Hispanic" aggregate)
    scatter_data = []
    for r in results:
        if r["median_household_income"] and r["bachelors_pct"] and r["code"] != "400":
            scatter_data.append({
                "x": round(r["bachelors_pct"], 1),
                "y": round(r["median_household_income"] / 1000, 1),  # in $K
                "label": r["short_label"],
                "category": "Hispanic Origin",
                "size": 50,  # uniform bubble size
            })

    # Sort by income descending for readability
    scatter_data.sort(key=lambda d: d["y"], reverse=True)

    # Step 4: Save outputs
    with open("hispanic_scatter_data.json", "w") as f:
        json.dump(scatter_data, f, indent=2)

    with open("hispanic_raw_data.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "code", "label", "median_household_income", "bachelors_pct"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "code": r["code"],
                "label": r["label"],
                "median_household_income": r["median_household_income"],
                "bachelors_pct": r["bachelors_pct"],
            })

    print(f"\n{'=' * 60}")
    print(f"Done! ACS {working_year} data for {len(scatter_data)} origin groups.")
    print(f"  → hispanic_scatter_data.json  (chart-ready scatter data)")
    print(f"  → hispanic_raw_data.csv       (raw data)")
    print(f"\nTo generate the chart, run:")
    print(f'  python generate_chart.py scatter hispanic_scatter_data.json \\')
    print(f'    "Argentines earn the most among US Hispanics" \\')
    print(f'    "Census Bureau ACS {working_year}" output.svg \\')
    print(f'    "Share with bachelor\'s degree (%)" \\')
    print(f'    "Median household income ($K)"')
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

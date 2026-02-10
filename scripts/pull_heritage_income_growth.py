#!/usr/bin/env python3
"""
Fetch historical median household income by heritage group from the Census Bureau
Selected Population Profiles (ACS 1-Year SPP) endpoint, going back to 2008.

Data source: US Census Bureau ACS 1-Year Selected Population Profiles
Endpoint: /data/{year}/acs/acs1/spp
Variable: Median household income (dollars) — variable name shifts by year

Available years: 2008-2024 (excluding 2010 and 2020)
  - 2010: Server error (Census API bug)
  - 2020: No ACS 1-Year released due to COVID-19 data collection issues

POPGROUP code format change:
  - 2008-2022: 3-digit codes (401=Mexican, 402=Puerto Rican, etc.)
  - 2023-2024: 4-digit codes (4015=Mexican, 4038=Puerto Rican, etc.)

Income variable name changes:
  - 2008-2009: S0201_217E
  - 2011-2015, 2017-2024: S0201_214E
  - 2016: S0201_0214E (leading zero in suffix)

Output:
  - heritage_income_by_year.csv — raw data (year, group, income)
  - heritage_income_growth.csv — growth summary per group
  - heritage_income_growth.json — chart-ready JSON

Usage:
    python scripts/pull_heritage_income_growth.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.census_fetch import CensusFetcher, clean_value, save_csv, save_json

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Heritage groups with POPGROUP codes (old_code for <=2022, new_code for >=2023)
HERITAGE_GROUPS = [
    {"label": "Hispanic or Latino (any race)", "old_code": "400", "new_code": "400"},
    {"label": "Mexican",                       "old_code": "401", "new_code": "4015"},
    {"label": "Puerto Rican",                  "old_code": "402", "new_code": "4038"},
    {"label": "Cuban",                         "old_code": "403", "new_code": "4036"},
    {"label": "Dominican",                     "old_code": "405", "new_code": "4037"},
    {"label": "Costa Rican",                   "old_code": "407", "new_code": "4017"},
    {"label": "Guatemalan",                    "old_code": "408", "new_code": "4018"},
    {"label": "Honduran",                      "old_code": "409", "new_code": "4019"},
    {"label": "Nicaraguan",                    "old_code": "410", "new_code": "4020"},
    {"label": "Panamanian",                    "old_code": "411", "new_code": "4021"},
    {"label": "Salvadoran",                    "old_code": "412", "new_code": "4022"},
    {"label": "Argentinean",                   "old_code": "414", "new_code": "4025"},
    {"label": "Chilean",                       "old_code": "416", "new_code": "4027"},
    {"label": "Colombian",                     "old_code": "417", "new_code": "4028"},
    {"label": "Ecuadorian",                    "old_code": "418", "new_code": "4029"},
    {"label": "Peruvian",                      "old_code": "420", "new_code": "4031"},
    {"label": "Venezuelan",                    "old_code": "422", "new_code": "4033"},
    {"label": "Spaniard",                      "old_code": "423", "new_code": "4041"},
    {"label": "Brazilian",                     "old_code": "519", "new_code": "519"},
]

# Years with SPP data available (no 2010 due to API error, no 2020 due to COVID)
AVAILABLE_YEARS = [2008, 2009, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]

# Median household income variable name by year
def income_variable(year):
    if year <= 2009:
        return "S0201_217E"
    elif year == 2016:
        return "S0201_0214E"
    else:
        return "S0201_214E"

# POPGROUP code format cutoff: 3-digit for <=2022, 4-digit for >=2023
def popgroup_code(group, year):
    if year >= 2023:
        return group["new_code"]
    else:
        return group["old_code"]


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_all_data(fetcher):
    """Fetch median household income for all heritage groups across all years."""
    records = []
    total_requests = len(AVAILABLE_YEARS) * len(HERITAGE_GROUPS)
    completed = 0

    for year in AVAILABLE_YEARS:
        var = income_variable(year)
        for group in HERITAGE_GROUPS:
            code = popgroup_code(group, year)
            completed += 1

            data = fetcher.fetch(
                year, "acs1_spp",
                ["NAME", var],
                geo_for="us:1",
                extra_params={"POPGROUP": code},
            )

            if data and len(data) > 0:
                income = clean_value(data[0].get(var))
                if income is not None:
                    records.append({
                        "year": year,
                        "group": group["label"],
                        "popgroup_code": code,
                        "median_household_income": int(income),
                    })
                    print(f"  [{completed}/{total_requests}] {year} {group['label']}: ${int(income):,}")
                else:
                    print(f"  [{completed}/{total_requests}] {year} {group['label']}: null value")
            else:
                print(f"  [{completed}/{total_requests}] {year} {group['label']}: no data")

            # Brief pause to be polite to the API
            time.sleep(0.1)

    return records


# ---------------------------------------------------------------------------
# Growth analysis
# ---------------------------------------------------------------------------

def compute_growth(records):
    """Compute income growth metrics for each heritage group."""
    # Organize by group
    by_group = {}
    for r in records:
        g = r["group"]
        if g not in by_group:
            by_group[g] = {}
        by_group[g][r["year"]] = r["median_household_income"]

    growth_records = []
    for group_label, year_data in sorted(by_group.items()):
        years = sorted(year_data.keys())
        if len(years) < 2:
            continue

        earliest_year = years[0]
        latest_year = years[-1]
        earliest_income = year_data[earliest_year]
        latest_income = year_data[latest_year]

        # Total growth
        total_growth_pct = ((latest_income - earliest_income) / earliest_income) * 100

        # Annualized (CAGR)
        n_years = latest_year - earliest_year
        if n_years > 0 and earliest_income > 0:
            cagr = ((latest_income / earliest_income) ** (1 / n_years) - 1) * 100
        else:
            cagr = 0

        # Year-over-year changes
        yoy_changes = []
        for i in range(1, len(years)):
            prev_y = years[i - 1]
            curr_y = years[i]
            prev_inc = year_data[prev_y]
            curr_inc = year_data[curr_y]
            if prev_inc > 0:
                yoy_pct = ((curr_inc - prev_inc) / prev_inc) * 100
                yoy_changes.append(yoy_pct)

        avg_yoy = sum(yoy_changes) / len(yoy_changes) if yoy_changes else 0

        growth_records.append({
            "group": group_label,
            "earliest_year": earliest_year,
            "earliest_income": earliest_income,
            "latest_year": latest_year,
            "latest_income": latest_income,
            "total_growth_pct": round(total_growth_pct, 1),
            "cagr_pct": round(cagr, 2),
            "avg_yoy_pct": round(avg_yoy, 1),
            "years_of_data": len(years),
        })

    # Sort by total growth descending
    growth_records.sort(key=lambda x: x["total_growth_pct"], reverse=True)
    return growth_records


def build_chart_json(records):
    """Build chart-ready JSON with time series per group."""
    by_group = {}
    for r in records:
        g = r["group"]
        if g not in by_group:
            by_group[g] = []
        by_group[g].append({
            "year": r["year"],
            "income": r["median_household_income"],
        })

    series = []
    for group_label in sorted(by_group.keys()):
        points = sorted(by_group[group_label], key=lambda x: x["year"])
        series.append({
            "group": group_label,
            "data": points,
        })

    return series


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Fetching historical median household income by heritage group...")
    print(f"Years: {AVAILABLE_YEARS[0]}-{AVAILABLE_YEARS[-1]} ({len(AVAILABLE_YEARS)} data points)")
    print(f"Groups: {len(HERITAGE_GROUPS)}")
    print(f"Note: 2010 excluded (Census API error), 2020 excluded (no ACS 1-Year due to COVID)")
    print()

    fetcher = CensusFetcher()
    records = fetch_all_data(fetcher)

    print(f"\nCollected {len(records)} data points.")

    # Save raw data
    save_csv(
        records, "heritage_income_by_year.csv",
        fields=["year", "group", "popgroup_code", "median_household_income"],
    )

    # Compute and save growth analysis
    growth = compute_growth(records)
    save_csv(
        growth, "heritage_income_growth.csv",
        fields=["group", "earliest_year", "earliest_income", "latest_year",
                "latest_income", "total_growth_pct", "cagr_pct", "avg_yoy_pct",
                "years_of_data"],
    )

    # Save chart-ready JSON
    chart_data = build_chart_json(records)
    save_json(chart_data, "heritage_income_growth.json")

    # Print summary
    print("\n" + "=" * 80)
    print("INCOME GROWTH BY HERITAGE GROUP (sorted by total growth)")
    print("=" * 80)
    print(f"{'Group':<35} {'From':>6} {'To':>6} {'Start $':>10} {'End $':>10} {'Growth':>8} {'CAGR':>6}")
    print("-" * 80)
    for g in growth:
        print(
            f"{g['group']:<35} {g['earliest_year']:>6} {g['latest_year']:>6} "
            f"${g['earliest_income']:>8,} ${g['latest_income']:>8,} "
            f"{g['total_growth_pct']:>7.1f}% {g['cagr_pct']:>5.2f}%"
        )
    print("-" * 80)
    print(f"CAGR = Compound Annual Growth Rate")
    print(f"All values in nominal dollars (not inflation-adjusted)")


if __name__ == "__main__":
    main()

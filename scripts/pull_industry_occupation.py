#!/usr/bin/env python3
"""
Fetch industry and occupation breakdown by heritage group from the Census Bureau
Selected Population Profiles (ACS 1-Year SPP) endpoint.

Data source: US Census Bureau ACS 1-Year Selected Population Profiles
Endpoint: /data/{year}/acs/acs1/spp
Variables: S0201_176E-181E (occupation), S0201_194E-207E (industry)

All sub-category values are percentages of the civilian employed population
16 years and over. The total (S0201_176E / S0201_194E) is a count.

POPGROUP code format (same as income analysis):
  - 2024 uses 4-digit codes (4015=Mexican, 4038=Puerto Rican, etc.)
  - Major demographic groups use stable codes (001=Total, 451=White, etc.)

Output:
  - industry_by_group.csv — industry % breakdown per group
  - occupation_by_group.csv — occupation % breakdown per group
  - industry_occupation.json — chart-ready JSON with both breakdowns

Usage:
    python scripts/pull_industry_occupation.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.census_fetch import CensusFetcher, clean_value, save_csv, save_json

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

YEAR = 2024

# Same groups as heritage income growth analysis
DEMOGRAPHIC_GROUPS = [
    {"label": "Total US population",                          "code": "001"},
    {"label": "White alone, not Hispanic or Latino",          "code": "451"},
    {"label": "Black or African American alone, non-Hispanic", "code": "453"},
    {"label": "Asian alone, not Hispanic or Latino",          "code": "457"},
    {"label": "AIAN alone, not Hispanic or Latino",           "code": "455"},
    {"label": "NHPI alone, not Hispanic or Latino",           "code": "459"},
]

HERITAGE_GROUPS = [
    {"label": "Hispanic or Latino (any race)", "code": "400"},
    {"label": "Mexican",                       "code": "4015"},
    {"label": "Puerto Rican",                  "code": "4038"},
    {"label": "Cuban",                         "code": "4036"},
    {"label": "Dominican",                     "code": "4037"},
    {"label": "Costa Rican",                   "code": "4017"},
    {"label": "Guatemalan",                    "code": "4018"},
    {"label": "Honduran",                      "code": "4019"},
    {"label": "Nicaraguan",                    "code": "4020"},
    {"label": "Panamanian",                    "code": "4021"},
    {"label": "Salvadoran",                    "code": "4022"},
    {"label": "Argentinean",                   "code": "4025"},
    {"label": "Chilean",                       "code": "4027"},
    {"label": "Colombian",                     "code": "4028"},
    {"label": "Ecuadorian",                    "code": "4029"},
    {"label": "Peruvian",                      "code": "4031"},
    {"label": "Venezuelan",                    "code": "4033"},
    {"label": "Spaniard",                      "code": "4041"},
    {"label": "Brazilian",                     "code": "519"},
]

ALL_GROUPS = DEMOGRAPHIC_GROUPS + HERITAGE_GROUPS

# Occupation variables (2024) — percentages of civilian employed pop 16+
OCCUPATION_VARS = {
    "S0201_176E": "total_employed",
    "S0201_177E": "Management, business, science, and arts",
    "S0201_178E": "Service",
    "S0201_179E": "Sales and office",
    "S0201_180E": "Natural resources, construction, and maintenance",
    "S0201_181E": "Production, transportation, and material moving",
}

# Industry variables (2024) — percentages of civilian employed pop 16+
INDUSTRY_VARS = {
    "S0201_194E": "total_employed",
    "S0201_195E": "Agriculture, forestry, fishing, hunting, and mining",
    "S0201_196E": "Construction",
    "S0201_197E": "Manufacturing",
    "S0201_198E": "Wholesale trade",
    "S0201_199E": "Retail trade",
    "S0201_200E": "Transportation and warehousing, and utilities",
    "S0201_201E": "Information",
    "S0201_202E": "Finance, insurance, real estate, and leasing",
    "S0201_203E": "Professional, scientific, management, and admin services",
    "S0201_204E": "Educational services, health care, and social assistance",
    "S0201_205E": "Arts, entertainment, recreation, accommodation, and food",
    "S0201_206E": "Other services (except public administration)",
    "S0201_207E": "Public administration",
}

ALL_VARS = list(OCCUPATION_VARS.keys()) + [v for v in INDUSTRY_VARS.keys() if v != "S0201_194E"]


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_all_data(fetcher):
    """Fetch industry and occupation data for all groups."""
    industry_records = []
    occupation_records = []
    total = len(ALL_GROUPS)

    for i, group in enumerate(ALL_GROUPS, 1):
        data = fetcher.fetch(
            YEAR, "acs1_spp",
            ["NAME"] + ALL_VARS,
            geo_for="us:1",
            extra_params={"POPGROUP": group["code"]},
        )

        if data and len(data) > 0:
            row = data[0]
            total_employed = clean_value(row.get("S0201_176E"))
            employed_str = f"{int(total_employed):,}" if total_employed else "N/A"
            print(f"  [{i}/{total}] {group['label']}: {employed_str} employed")

            # Build occupation record
            occ_rec = {"group": group["label"], "total_employed": int(total_employed) if total_employed else None}
            for var, label in OCCUPATION_VARS.items():
                if label == "total_employed":
                    continue
                val = clean_value(row.get(var))
                occ_rec[label] = round(val, 1) if val is not None else None
            occupation_records.append(occ_rec)

            # Build industry record
            ind_rec = {"group": group["label"], "total_employed": int(total_employed) if total_employed else None}
            for var, label in INDUSTRY_VARS.items():
                if label == "total_employed":
                    continue
                val = clean_value(row.get(var))
                ind_rec[label] = round(val, 1) if val is not None else None
            industry_records.append(ind_rec)
        else:
            print(f"  [{i}/{total}] {group['label']}: no data")

        time.sleep(0.1)

    return industry_records, occupation_records


# ---------------------------------------------------------------------------
# Chart JSON
# ---------------------------------------------------------------------------

def build_chart_json(industry_records, occupation_records):
    """Build chart-ready JSON with both industry and occupation breakdowns."""
    industry_categories = [label for label in INDUSTRY_VARS.values() if label != "total_employed"]
    occupation_categories = [label for label in OCCUPATION_VARS.values() if label != "total_employed"]

    chart = {
        "year": YEAR,
        "industry": {
            "categories": industry_categories,
            "groups": [],
        },
        "occupation": {
            "categories": occupation_categories,
            "groups": [],
        },
    }

    for rec in industry_records:
        chart["industry"]["groups"].append({
            "group": rec["group"],
            "total_employed": rec["total_employed"],
            "values": [rec.get(cat) for cat in industry_categories],
        })

    for rec in occupation_records:
        chart["occupation"]["groups"].append({
            "group": rec["group"],
            "total_employed": rec["total_employed"],
            "values": [rec.get(cat) for cat in occupation_categories],
        })

    return chart


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Fetching industry & occupation breakdown by heritage group ({YEAR})...")
    print(f"Groups: {len(ALL_GROUPS)} ({len(DEMOGRAPHIC_GROUPS)} demographic + {len(HERITAGE_GROUPS)} heritage)")
    print()

    fetcher = CensusFetcher()
    industry_records, occupation_records = fetch_all_data(fetcher)

    print(f"\nCollected data for {len(industry_records)} groups.")

    # Save industry CSV
    industry_fields = ["group", "total_employed"] + [
        label for label in INDUSTRY_VARS.values() if label != "total_employed"
    ]
    save_csv(industry_records, "industry_by_group.csv", fields=industry_fields)

    # Save occupation CSV
    occupation_fields = ["group", "total_employed"] + [
        label for label in OCCUPATION_VARS.values() if label != "total_employed"
    ]
    save_csv(occupation_records, "occupation_by_group.csv", fields=occupation_fields)

    # Save combined CSV (all occupation + industry columns in one file)
    occ_labels = [label for label in OCCUPATION_VARS.values() if label != "total_employed"]
    ind_labels = [label for label in INDUSTRY_VARS.values() if label != "total_employed"]
    combined_fields = ["group", "total_employed"] + \
        [f"occ: {l}" for l in occ_labels] + \
        [f"ind: {l}" for l in ind_labels]
    combined_records = []
    for occ_rec, ind_rec in zip(occupation_records, industry_records):
        row = {"group": occ_rec["group"], "total_employed": occ_rec["total_employed"]}
        for l in occ_labels:
            row[f"occ: {l}"] = occ_rec.get(l)
        for l in ind_labels:
            row[f"ind: {l}"] = ind_rec.get(l)
        combined_records.append(row)
    save_csv(combined_records, "industry_occupation_by_group.csv", fields=combined_fields)

    # Save chart-ready JSON
    chart_data = build_chart_json(industry_records, occupation_records)
    save_json(chart_data, "industry_occupation.json")

    # Print industry summary
    w = 160
    print("\n" + "=" * w)
    print(f"INDUSTRY BREAKDOWN BY GROUP ({YEAR}) — % of civilian employed population 16+")
    print("=" * w)

    # Abbreviated column headers for readability
    ind_short = ["Ag/Mine", "Constr", "Mfg", "Whsale", "Retail", "Trans", "Info",
                 "Fin/RE", "Prof/Sci", "Edu/Hlth", "Arts/Food", "Other", "Pub Adm"]
    ind_labels = [label for label in INDUSTRY_VARS.values() if label != "total_employed"]

    header = f"{'Group':<48} {'Employed':>12}  " + "  ".join(f"{h:>9}" for h in ind_short)
    print(header)
    print("-" * w)
    for rec in industry_records:
        emp = f"{rec['total_employed']:>12,}" if rec['total_employed'] else "         N/A"
        vals = "  ".join(
            f"{rec.get(lab, 0) or 0:>8.1f}%" for lab in ind_labels
        )
        print(f"{rec['group']:<48} {emp}  {vals}")

    # Print occupation summary
    print("\n" + "=" * w)
    print(f"OCCUPATION BREAKDOWN BY GROUP ({YEAR}) — % of civilian employed population 16+")
    print("=" * w)
    occ_short = ["Mgmt/Sci", "Service", "Sales/Off", "NatRes/Constr", "Prod/Trans"]
    occ_labels = [label for label in OCCUPATION_VARS.values() if label != "total_employed"]

    header = f"{'Group':<48} {'Employed':>12}  " + "  ".join(f"{h:>13}" for h in occ_short)
    print(header)
    print("-" * w)
    for rec in occupation_records:
        emp = f"{rec['total_employed']:>12,}" if rec['total_employed'] else "         N/A"
        vals = "  ".join(
            f"{rec.get(lab, 0) or 0:>12.1f}%" for lab in occ_labels
        )
        print(f"{rec['group']:<48} {emp}  {vals}")

    print("-" * w)
    print(f"Source: US Census Bureau, ACS 1-Year Selected Population Profiles ({YEAR})")
    print(f"All values are percentages of civilian employed population 16 years and over")


if __name__ == "__main__":
    main()

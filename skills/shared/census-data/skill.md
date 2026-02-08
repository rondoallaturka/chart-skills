---
name: census-data
description: Fetch US Census Bureau data via the public API with iterative discovery
version: 1.0.0
author: chart-skills
tags: [census, demographics, economics, government-data, api]
---

# Census Data Fetcher

Fetch demographic, economic, and social data from the US Census Bureau API. The Census API is powerful but has many quirks — variable names shift between years, endpoints differ by table type, and geography nesting rules vary. This skill encodes the knowledge needed to navigate that iteratively.

## Usage

```
/census-data <description of what data you need>
```

### Examples

```
/census-data median household income by state
/census-data poverty rate by county in California
/census-data population by race for all zip codes
/census-data bachelor's degree attainment by congressional district
/census-data housing vacancy rates by metro area
/census-data Hispanic origin groups income and education
```

## Instructions

When the user invokes this skill, follow the **iterative discovery workflow** below. Census API calls frequently fail on the first attempt — this is normal and expected. The skill is designed around a probe-and-adjust loop.

### Step 1: Identify the right dataset and endpoint

The Census API has multiple datasets, each with sub-endpoints. Match the user's request:

| User wants | Dataset | Endpoint pattern |
|------------|---------|-----------------|
| Demographic/economic stats (recent, all areas) | ACS 5-Year | `/data/{year}/acs/acs5` |
| Demographic/economic stats (recent, large areas only) | ACS 1-Year | `/data/{year}/acs/acs1` |
| Summary statistics (pre-computed %) | ACS Subject Tables | `/data/{year}/acs/acs5/subject` |
| Curated profile indicators | ACS Data Profiles | `/data/{year}/acs/acs5/profile` |
| Comparison across years | ACS Comparison Profiles | `/data/{year}/acs/acs5/cprofile` |
| Data by population subgroup (race, ancestry, origin) | ACS Selected Population Profiles | `/data/{year}/acs/acs1/spp` |
| Official population counts | Decennial Census | `/data/2020/dec/pl` |
| Business/employer statistics | County Business Patterns | `/data/{year}/cbp` |
| Annual population estimates | Population Estimates | `/data/{year}/pep/population` |

**Base URL**: `https://api.census.gov`

**Year guidance**:
- ACS 5-Year: Use 2023 (latest). Covers all geographies including small areas.
- ACS 1-Year: Use 2024 or 2023. Only covers areas with population 65,000+.
- Decennial: Use 2020. Next will be 2030.
- CBP: Use 2022 (latest).
- PEP: Variable names and endpoints shift frequently. Probe first.

### Step 2: Find the right variable names

**This is where most failures happen.** Variable names change between years and table types.

#### Discovery method: Use the variables endpoint

```
https://api.census.gov/data/{year}/acs/acs5/variables.json
```

This returns all available variables with labels. Search it programmatically:

```python
import requests
url = "https://api.census.gov/data/2023/acs/acs5/variables.json"
r = requests.get(url, timeout=30)
variables = r.json()["variables"]

# Search for variables by keyword
for name, info in variables.items():
    label = info.get("label", "").lower()
    if "median" in label and "household" in label and "income" in label:
        print(f"{name}: {info['label']}")
```

#### Common variable cheat sheet

These are known-good for 2023. Always verify with the variables endpoint.

**ACS Detailed Tables** (`/acs/acs5` or `/acs/acs1`):
| Variable | Description |
|----------|-------------|
| `B01001_001E` | Total population |
| `B19013_001E` | Median household income |
| `B02001_001E` through `_006E` | Population by race |
| `B25077_001E` | Median home value |
| `B25064_001E` | Median gross rent |
| `B15003_022E` | Bachelor's degree holders |
| `B23025_005E` | Unemployed population |
| `B27001_001E` | Health insurance universe |

**ACS Subject Tables** (`/acs/acs5/subject`):
| Variable | Description |
|----------|-------------|
| `S1701_C03_001E` | Poverty rate (%) |
| `S1501_C02_015E` | % bachelor's degree or higher |
| `S2301_C04_001E` | Unemployment rate (%) |

**ACS Data Profiles** (`/acs/acs5/profile`):
| Variable | Description |
|----------|-------------|
| `DP03_0062E` | Median household income |
| `DP03_0096PE` | % with health insurance |
| `DP04_0089E` | Median home value |
| `DP05_0001E` | Total population |

**Selected Population Profiles** (`/acs/acs1/spp`):
| Variable | Description |
|----------|-------------|
| `S0201_214E` | Median household income |
| `S0201_099E` | % bachelor's degree or higher |
| Requires `POPGROUP` parameter | See Step 4 |

### Step 3: Construct the geography

The `for` parameter specifies what geographic level to fetch. Some levels require a parent via `in`.

| Geography | `for` parameter | Requires `in` |
|-----------|----------------|---------------|
| Entire US | `us:1` | — |
| All states | `state:*` | — |
| One state | `state:06` (FIPS code) | — |
| All counties | `county:*` | `state:{fips}` (one state) or omit `in` for all |
| All tracts | `tract:*` | `state:{fips}&in=county:{fips}` |
| All ZCTAs (zip codes) | `zip code tabulation area:*` | — (5-year only) |
| Congressional districts | `congressional district:*` | — or `state:{fips}` |
| Metro areas (CBSAs) | `metropolitan statistical area/micropolitan statistical area:*` | — |
| Places (cities/towns) | `place:*` | `state:{fips}` |

**FIPS codes**: California=06, Texas=48, New York=36, Florida=12, Illinois=17, etc.

### Step 4: Handle special parameters

#### POPGROUP (Selected Population Profiles only)

The `/spp` endpoint requires a `POPGROUP` parameter. These codes identify population subgroups.

**Discovery method**:
```python
url = "https://api.census.gov/data/2023/acs/acs1/spp/variables/POPGROUP.json"
r = requests.get(url, timeout=15)
items = r.json()["values"]["item"]
# Search by keyword
for code, label in items.items():
    if "mexican" in label.lower():
        print(f"{code}: {label}")
```

**Known codes (as of 2024)**:
| Code | Group |
|------|-------|
| `001` | Total population |
| `400` | Hispanic or Latino (of any race) |
| `4015` | Mexican |
| `4038` | Puerto Rican |
| `4036` | Cuban |
| `4037` | Dominican |
| `4025` | Argentinean |
| `4028` | Colombian |
| `4033` | Venezuelan |
| `519` | Brazilian |

**Warning**: Older Census documentation uses 3-digit codes (401, 416, etc.) that now return HTTP 204. Always use the 4-digit codes listed above or discover them via the variables endpoint.

#### API Key

No key is needed for light usage. For heavy queries or reliability:
```
&key=YOUR_KEY
```
Get a free key at: https://api.census.gov/data/key_signup.html

### Step 5: Make the request (expect iteration)

#### First attempt pattern

```python
import requests

url = "https://api.census.gov/data/2023/acs/acs5"
params = {
    "get": "NAME,B19013_001E",
    "for": "state:*",
}
r = requests.get(url, params=params, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    # data[0] is the header row, data[1:] are data rows
    print(f"Header: {data[0]}")
    print(f"First row: {data[1]}")
else:
    print(f"Error: {r.text}")
```

#### When it fails (and it will)

| Error | Meaning | Fix |
|-------|---------|-----|
| `400: unknown variable` | Variable name wrong for this endpoint/year | Search the variables endpoint |
| `400: unknown predicate variable` | Parameter not supported (e.g., POPGROUP on non-spp) | Switch endpoint |
| `204: No Content` | Valid request but no data for this combination | Try different year, different geography, or different group code |
| `404: Not Found` | Endpoint doesn't exist for this year | Check available years |

**The probe-and-adjust loop**:

1. Try the request
2. If it fails, diagnose from the error
3. Search the variables endpoint for the correct variable name
4. Adjust and retry
5. Once one working request is confirmed, use the same variables for remaining queries

### Step 6: Process and save results

```python
import csv, json

# Census API returns [header, row1, row2, ...]
data = r.json()
header = data[0]
rows = data[1:]

# Save as CSV
with open("output.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

# Or convert to list of dicts
records = [dict(zip(header, row)) for row in rows]
with open("output.json", "w") as f:
    json.dump(records, f, indent=2)
```

### Step 7: Save a reusable script

After the iterative discovery succeeds, save a clean Python script with:
- The confirmed working endpoint, variables, and parameters
- Docstring documenting the data source and year
- CSV and JSON output
- Clear variable names so the user can adapt it later

## Brainstorm: Types of Data Available

The Census API covers far more than demographics. Here are chart-worthy datasets:

### Income & Inequality
- Median household income by state/county/metro
- Income distribution brackets (B19001 series)
- Gini index by geography (B19083_001E)
- Poverty rates by age, race, family type

### Education
- Educational attainment by geography
- School enrollment by level
- Field of degree for bachelor's holders (B15012 series)

### Housing
- Median home values and rents by geography
- Homeownership rates by race/age
- Housing vacancy rates
- Year structure built (age of housing stock)
- Monthly housing costs as % of income

### Employment & Business
- Unemployment rates by geography
- Industry of employment (NAICS sectors)
- County Business Patterns: establishment counts, payroll, employees by industry
- Commute time and mode of transportation

### Demographics
- Population by race/ethnicity at any geography level
- Age distribution pyramids
- Foreign-born population by origin
- Language spoken at home
- Ancestry groups (e.g., German, Irish, Italian by county)

### Health
- Health insurance coverage rates
- Disability status by type
- Veteran status

### Migration & Mobility
- Geographic mobility (moved in past year)
- Place of birth vs current residence
- Citizenship status

## Common Pitfalls (Lessons Learned)

1. **Subject tables (`S*`) live in `/subject`, not the base endpoint** — but Selected Population Profiles (`S0201`) live in `/spp`
2. **Variable names are NOT stable across years** — always verify against the variables endpoint for your target year
3. **ACS 1-Year only covers areas with 65,000+ population** — use 5-Year for small geographies
4. **POPGROUP codes changed** — old 3-digit codes (401, 416, etc.) return 204; use 4-digit codes (4015, 4038, etc.)
5. **Geography nesting** — counties need `in=state:XX`, tracts need both state and county
6. **PEP endpoint is unstable** — variable names and URL structure change frequently between years
7. **The `E` suffix means Estimate** — `M` is margin of error, `PE` is percent estimate
8. **No API key needed for light use** — but rate limits apply; add a key for batch queries
9. **Puerto Rico ZCTAs are included** in ZCTA queries — filter by FIPS prefix if needed
10. **NULL values** appear as `"-"`, `"N"`, `"(X)"`, `null`, or empty string — handle all cases

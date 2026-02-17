# Latino/Hispanic Entrepreneurship: Value Added Through Employment & Business

Metrics and data sources for estimating the entrepreneurship value added by
Hispanic/Latino (and Brazilian) populations in the US, including employer
firms, job creation, revenue, and self-employment.

## Data Sources

Three Census programs provide entrepreneurship data, each with different
strengths:

| Source | What it measures | Hispanic breakdown | Geography | Years |
|--------|-----------------|-------------------|-----------|-------|
| **Annual Business Survey (ABS)** | Employer firms: count, revenue, employees, payroll, industry | Yes (`ETH_GROUP=020`) | US, state, metro, county | 2018–2023 |
| **Nonemployer Statistics by Demographics (NES-D)** | Sole proprietorships with no employees: count, revenue | Yes (by ethnicity) | US, state, metro, county | 2017+ |
| **ACS Selected Population Profiles (SPP)** | Self-employment rate, class of worker | Yes, by origin group (POPGROUP) | US, state | 2005–2024 |

**Key limitation:** The ABS and NES-D only distinguish Hispanic vs.
non-Hispanic — they do NOT break down by origin group (Mexican, Cuban,
etc.). Only the ACS/SPP can do origin-group splits, but it only captures
self-employment *rate*, not firm-level data like revenue or employees.

---

## 1. Employer Firm Data (ABS Company Summary)

### API Endpoint

```
https://api.census.gov/data/{year}/abscs
```

Key variables: `FIRMPDEMP` (firms), `RCPPDEMP` (revenue, $1000s), `EMP`
(employees), `PAYANN` (payroll, $1000s), `ETH_GROUP`, `NAICS2022`.

### National Totals (2023, reference year)

| Metric | Hispanic | All Firms | Hispanic Share |
|--------|---------|-----------|---------------|
| **Employer firms** | 495,822 | 5,934,950 | **8.4%** |
| **Revenue** | $730.3B | $48.2T | **1.5%** |
| **Employees** | 3,822,895 | 132,849,544 | **2.9%** |
| **Annual payroll** | $160.2B | $8.9T | **1.8%** |

### Growth Trend (2021 → 2023)

| Metric | 2021 | 2022 | 2023 | Growth (2yr) |
|--------|------|------|------|-------------|
| Firms | 406,086 | 465,202 | 495,822 | **+22.1%** |
| Revenue ($B) | $572.9 | $653.5 | $730.3 | **+27.5%** |
| Employees | 2,985,954 | 3,550,203 | 3,822,895 | **+28.0%** |
| Payroll ($B) | $124.4 | $143.2 | $160.2 | **+28.8%** |

Hispanic employer firms are growing significantly faster than the overall
business population.

### Top Industries by Firm Count (2023, Hispanic employer firms)

| Rank | Sector | Firms | Revenue | Employees |
|------|--------|-------|---------|-----------|
| 1 | **Construction** | 96,656 | $141.1B | 482,173 |
| 2 | **Accommodation & food services** | 61,069 | $72.5B | 825,358 |
| 3 | **Professional/scientific/technical** | 53,222 | $50.6B | 269,713 |
| 4 | **Admin/support/waste management** | 48,444 | $54.5B | 599,300 |
| 5 | **Health care & social assistance** | 42,951 | $38.8B | 419,151 |
| 6 | **Retail trade** | 38,273 | $107.9B | 282,694 |
| 7 | **Other services** | 36,802 | $21.2B | 141,899 |
| 8 | **Transportation & warehousing** | 32,307 | $34.5B | 185,719 |

Notable sub-sectors:
- **Restaurants** alone: 54,549 firms, $68.1B revenue, 785,674 employees
- **Specialty trade contractors**: 68,009 firms, $89.1B revenue
- **Services to buildings/dwellings** (landscaping, janitorial): 36,437
  firms, $28.6B revenue, 259,771 employees

### Calculating Value Added

Value added = Revenue minus cost of intermediate inputs. Census doesn't
publish value-added by owner ethnicity directly, but we can estimate it:

```
Method: Industry-weighted value-added ratio

For each NAICS sector where Hispanic firms operate:
  1. Get Hispanic firm revenue from ABS
  2. Get the sector's value-added-to-revenue ratio from BEA GDP-by-Industry
  3. Multiply: Hispanic VA = Hispanic Revenue × (Sector VA / Sector Revenue)
  4. Sum across all sectors

Rough estimate using economy-wide average (~50% VA/revenue ratio):
  $730.3B × 0.50 ≈ $365B in value added from employer firms alone
```

This is conservative — construction and services (where Hispanic firms
concentrate) tend to have higher value-added ratios than manufacturing.

---

## 2. Nonemployer Firms (Sole Proprietorships)

The ABS only covers employer firms (those with paid employees). But a huge
portion of Hispanic entrepreneurship is in **nonemployer businesses** — sole
proprietorships, freelancers, gig workers, independent contractors.

### Nonemployer Statistics by Demographics (NES-D)

From the Census Bureau's 2024 press release:
- **5.3 million** Hispanic-owned nonemployer businesses (17.5% of all
  nonemployer firms)
- **$244.2 billion** in receipts

### Combined Picture (Employer + Nonemployer, 2023)

| Type | Firms | Revenue |
|------|-------|---------|
| Employer firms | 495,822 | $730.3B |
| Nonemployer firms | ~5,300,000 | ~$244.2B |
| **Total** | **~5,800,000** | **~$974.5B** |

Nearly **$1 trillion** in total business revenue from Hispanic-owned firms.

---

## 3. Self-Employment by Origin Group (ACS/SPP)

The ABS can't distinguish between Mexican-owned vs. Cuban-owned firms. But
the ACS Selected Population Profiles can measure self-employment *rates* by
origin group.

### Class of Worker Breakdown (SPP, 2023)

**Hispanic/Latino overall** (POPGROUP=400, 31.3M civilian employed):

| Class of Worker | Share |
|----------------|-------|
| Private wage & salary | 81.5% |
| Government | 11.4% |
| **Self-employed (not incorporated)** | **6.9%** |
| Unpaid family workers | 0.2% |

**Brazilian** (POPGROUP=519, 327,217 civilian employed):

| Class of Worker | Share |
|----------------|-------|
| Private wage & salary | 77.7% |
| Government | 6.8% |
| **Self-employed (not incorporated)** | **15.2%** |
| Unpaid family workers | 0.2% |

Brazilians have a self-employment rate **more than double** the Hispanic
average (15.2% vs. 6.9%).

### Estimating Self-Employed Workers by Origin Group

Using population and employment data from SPP:

```
Hispanic civilian employed: 31,302,826
Hispanic self-employed: 31,302,826 × 6.9% ≈ 2,159,895

Brazilian civilian employed: 327,217
Brazilian self-employed: 327,217 × 15.2% ≈ 49,737
```

### Origin-Group Comparison (requires pulling for each POPGROUP)

To compare entrepreneurship rates across origin groups, fetch S0201_211E
for each POPGROUP:

```bash
# Mexican
python scripts/census_fetch.py fetch 2023 acs1_spp \
  "NAME,S0201_208E,S0201_211E" "us:1" --param POPGROUP=4015

# Cuban
python scripts/census_fetch.py fetch 2023 acs1_spp \
  "NAME,S0201_208E,S0201_211E" "us:1" --param POPGROUP=4036

# Colombian, Venezuelan, Dominican, etc.
```

Historically, **Cubans** have the highest self-employment rate among
Hispanic origin groups, driven by the Miami business ecosystem and earlier
immigration waves that brought entrepreneurial capital.

---

## 4. Employment Multiplier: Jobs Created

Hispanic-owned employer firms employ **3.82 million workers** (2023 ABS).
These are not all Hispanic workers — Hispanic-owned firms employ people of
all backgrounds.

### Job Creation Value

```
Direct employment:                   3,822,895 workers
Annual payroll:                       $160.2 billion
Average wage per employee:            $41,913

For context:
  Total US employer firm employees:   132,849,544
  Hispanic firm share of employment:  2.9%
  Hispanic firm share of firm count:  8.4%
```

The gap between firm count share (8.4%) and employment share (2.9%)
reflects that Hispanic-owned firms are typically smaller. Average employees
per firm: 7.7 (vs. 22.4 for all firms).

### Employment Growth

Hispanic-owned firms added **836,941 jobs** from 2021 to 2023 — a 28%
increase in two years. This outpaces overall employer firm job growth.

---

## 5. What We Can and Can't Estimate

### Can estimate from Census data:

| Metric | Source | Available |
|--------|--------|-----------|
| Number of Hispanic employer firms | ABS | Yes, by state/metro/industry |
| Revenue of Hispanic employer firms | ABS | Yes |
| Employees at Hispanic firms | ABS | Yes |
| Annual payroll of Hispanic firms | ABS | Yes |
| Nonemployer firm count and revenue | NES-D | Yes |
| Self-employment rate by origin group | ACS/SPP | Yes (Mexican, Cuban, etc.) |
| Industry concentration | ABS | Yes, detailed NAICS |
| Growth over time | ABS (2018–2023) | Yes |
| Value added (estimated) | ABS revenue × BEA ratios | Approximate |
| Self-employment income (aggregate) | ACS B19063 | Total only; Hispanic TBD |

### Cannot estimate from Census data alone:

| Metric | Why not | Alternative source |
|--------|---------|-------------------|
| Brazilian-owned firm count/revenue | ABS only splits Hispanic/non-Hispanic | None via Census |
| Origin-group firm data (Mexican vs. Cuban) | ABS doesn't track origin group | Only self-employment rate via SPP |
| Indirect/induced employment multiplier | Requires input-output modeling | BEA RIMS II multipliers |
| Innovation metrics (patents, R&D) | Not in Census business surveys | USPTO, NSF |
| Venture capital / startup formation | Not in Census | PitchBook, Crunchbase |
| Informal economy contribution | Census only captures formal business | — |

---

## 6. Reproducibility

### ABS Company Summary

```bash
# All ethnicity groups, all industries, national (2023)
python3 -c "
import requests
url = 'https://api.census.gov/data/2023/abscs'
params = {
    'get': 'ETH_GROUP,ETH_GROUP_LABEL,FIRMPDEMP,RCPPDEMP,EMP,PAYANN',
    'for': 'us:*',
    'NAICS2022': '00',
}
r = requests.get(url, params=params, timeout=30)
for row in r.json(): print(row)
"

# Hispanic firms by industry (2023)
python3 -c "
import requests
url = 'https://api.census.gov/data/2023/abscs'
params = {
    'get': 'NAICS2022,NAICS2022_LABEL,FIRMPDEMP,RCPPDEMP,EMP,PAYANN',
    'for': 'us:*',
    'ETH_GROUP': '020',
}
r = requests.get(url, params=params, timeout=30)
for row in r.json(): print(row)
"

# Hispanic firms by state (2023)
python3 -c "
import requests
url = 'https://api.census.gov/data/2023/abscs'
params = {
    'get': 'NAME,FIRMPDEMP,RCPPDEMP,EMP,PAYANN',
    'for': 'state:*',
    'ETH_GROUP': '020',
    'NAICS2022': '00',
}
r = requests.get(url, params=params, timeout=30)
for row in r.json(): print(row)
"
```

### ACS Self-Employment by Origin Group

```bash
# Hispanic self-employment rate
python scripts/census_fetch.py fetch 2023 acs1_spp \
  "NAME,S0201_208E,S0201_209E,S0201_210E,S0201_211E,S0201_212E" "us:1" \
  --param POPGROUP=400

# Brazilian self-employment rate
python scripts/census_fetch.py fetch 2023 acs1_spp \
  "NAME,S0201_208E,S0201_209E,S0201_210E,S0201_211E,S0201_212E" "us:1" \
  --param POPGROUP=519
```

### Note on API Key

Several queries in this analysis hit rate limits. Register for a free key
at https://api.census.gov/data/key_signup.html and append `&key=YOUR_KEY`
to avoid throttling.

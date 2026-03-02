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

### Full Time Series (2018–2023, ABS)

| Year | Hispanic Firms | Hispanic Employees | All Firms | All Employees | Hisp % of Classified Emp |
|------|---------------|-------------------|-----------|---------------|------------------------|
| 2018 | 331,625 | 2,972,140 | 5,722,142 | 128,196,406 | 4.7% |
| 2019 | 346,836 | 2,930,548 | 5,771,292 | 128,898,226 | 4.6% |
| 2020 | 375,256 | 2,939,740 | 5,775,258 | 129,363,644 | 4.6% |
| 2021 | 406,086 | 2,985,954 | 5,893,425 | 123,935,338 | 4.8% |
| 2022 | 465,202 | 3,550,203 | 5,876,787 | 136,514,851 | 5.3% |
| 2023 | 495,822 | 3,822,895 | 5,934,950 | 132,849,544 | 5.8% |

Note: "Classified" employment = Hispanic + Non-Hispanic + Equally
Hispanic/Non-Hispanic. About half of all employer-firm employees work at
firms where the owner's ethnicity could be classified. The other half are
at publicly held companies, large corporations, or firms that didn't
report owner demographics.

### Hispanic Share of Net New Job Creation

This is the headline metric: **what percentage of net new employer-firm
jobs were created by Hispanic-owned businesses?**

| Time Span | Hispanic Net New Jobs | All Net New Jobs | Hispanic Share (All) | Hispanic Share (Classified) |
|-----------|---------------------|-----------------|---------------------|---------------------------|
| **2018→2023 (5yr)** | **+850,755** | +4,653,138 | **18.3%** | **32.2%** |
| 2019→2023 (pre-COVID base) | +892,347 | +3,951,318 | **22.6%** | **47.8%** |
| 2020→2023 (post-COVID) | +883,155 | +3,485,900 | **25.3%** | **42.5%** |
| 2021→2023 (recovery) | +836,941 | +8,914,206 | 9.4% | 18.9% |

Key findings:
- Over **5 years (2018→2023)**, Hispanic-owned firms created **850,755 net
  new jobs**, representing **18.3% of all net new employer-firm jobs** in
  the US — roughly 1 in 5.
- Among firms where ownership ethnicity is classified, the Hispanic share
  is even higher: **32.2%** of net new classified jobs.
- Hispanic-owned firms added **+164,197 net new firms** (2018→2023), which
  is **77.2% of all net new firms** in the country. The overall firm count
  grew by only 212,808 — Hispanic firms drove more than three-quarters of
  that growth.
- In 2022→2023, while total employer-firm employment *declined* by 3.67M,
  Hispanic-owned firms **still added +272,692 jobs** — counter-cyclical
  growth.

### Net New Firms: Hispanic-Owned Businesses Are the Growth Engine

| Time Span | Hispanic Net New Firms | All Net New Firms | Hispanic Share |
|-----------|----------------------|------------------|---------------|
| 2018→2023 | +164,197 (+49.5%) | +212,808 (+3.7%) | **77.2%** |
| 2019→2023 | +148,986 (+43.0%) | +163,658 (+2.8%) | **91.0%** |

From the pre-COVID baseline (2019), Hispanic-owned businesses account for
**91% of all net new employer firms** in the United States. Total firm
count barely grew (+2.8%), but Hispanic firms surged (+43%).

### Net New Payroll

| Time Span | Hispanic Net Payroll | All Net Payroll | Hispanic Share |
|-----------|---------------------|----------------|---------------|
| 2018→2023 | +$59.1B (+58.5%) | +$1,945.9B | 3.0% |
| 2019→2023 | +$51.9B (+47.9%) | +$1,655.5B | 3.1% |

Hispanic payroll share of net new payroll is lower (3%) than job share
(18%) because Hispanic firms tend to be smaller and in lower-wage sectors.
But Hispanic firm payroll grew **58.5%** vs. overall payroll growth of
28%.

### Year-over-Year Employment Changes

| Period | Hispanic Jobs | All Jobs | Hispanic % of Total | Hispanic Firms | All Firms |
|--------|-------------|----------|--------------------|-|-|
| 2018→2019 | -41,592 | +701,820 | -5.9% | +15,211 | +49,150 |
| 2019→2020 | +9,192 | +465,418 | 2.0% | +28,420 | +3,966 |
| 2020→2021 | +46,214 | -5,428,306 | counter-cyclical | +30,830 | +118,167 |
| 2021→2022 | +564,249 | +12,579,513 | 4.5% | +59,116 | -16,638 |
| 2022→2023 | +272,692 | -3,665,307 | counter-cyclical | +30,620 | +58,163 |

Hispanic-owned firm employment has been **counter-cyclical** — growing
even in years when overall employer-firm employment declined (2020→2021
and 2022→2023).

### 2022 Origin-Group Breakdown (only available year)

| Origin | Firms | Employees | Emp Share | Revenue | Avg Emp/Firm |
|--------|-------|-----------|-----------|---------|-------------|
| **Mexican/Chicano** | 230,511 | 1,963,327 | 56.9% | $341.5B | 8.5 |
| **Other Hispanic** | 157,405 | 965,046 | 28.0% | $185.8B | 6.1 |
| **Cuban** | 41,079 | 351,849 | 10.2% | $77.6B | 8.6 |
| **Puerto Rican** | 25,946 | 167,882 | 4.9% | $29.6B | 6.5 |

Mexican/Chicano-owned firms are the largest group (57% of Hispanic-owned
firm employment), but Cuban-owned firms have the highest average employees
per firm (8.6) and highest revenue per firm ($1.89M vs. $1.48M for Mexican).

---

## 1b. Net New Jobs & Firms by ALL Demographic Groups (2018 → 2023)

The ABS tracks four owner dimensions: **race**, **ethnicity**, **sex**,
and **veteran status**. This section shows which groups are creating jobs
and firms, and which are contracting.

**Total net new employer-firm jobs: +4,653,138**
**Total net new employer firms: +212,808**

### By Owner Race

| Group | Net New Jobs | % of Total | Job Growth | Net New Firms | % of Total | Firm Growth |
|-------|-------------|-----------|------------|--------------|-----------|-------------|
| **White** | +1,373,285 | 29.5% | +2.4% | +12,092 | 5.7% | +0.3% |
| **Black/African American** | +675,908 | 14.5% | **+56.9%** | +76,334 | 35.9% | **+61.3%** |
| **Asian** | +471,712 | 10.1% | +9.3% | +107,081 | 50.3% | +18.5% |
| **Amer. Indian/AK Native** | +163,249 | 3.5% | **+81.5%** | +30,685 | 14.4% | **+125.6%** |
| **Native HI/Pacific Isl.** | +8,082 | 0.2% | +14.8% | +2,760 | 1.3% | +41.5% |
| *Minority (composite)* | *+2,033,635* | *43.7%* | *+21.6%* | *+352,452* | *+165.6%* | *+33.6%* |
| *Nonminority* | *+480,114* | *10.3%* | *+0.9%* | *-161,844* | *-76.1%* | *-3.7%* |

Key patterns:
- **Black-owned firms** had the fastest job growth rate (56.9%) and
  added 675,908 jobs — 14.5% of all net new jobs.
- **AIAN-owned firms** had the fastest firm growth (125.6%, from
  24,433 to 55,118 firms) and fastest job growth (81.5%).
- **Asian-owned firms** added the most net new firms of any single
  race group (+107,081), accounting for 50.3% of all net new firms.
- **Nonminority-owned firms** added jobs (+480K) but **lost 161,844
  firms** — a net contraction of 3.7% in firm count. The existing
  nonminority firms got bigger, but fewer new ones formed.
- **Minority-owned firms** (composite) created **43.7% of all net new
  jobs** and **165.6% of net new firms** (the nonminority firm count
  shrank, so minorities produced more than 100% of net growth).

### By Owner Ethnicity

| Group | Net New Jobs | % of Total | Job Growth | Net New Firms | % of Total | Firm Growth |
|-------|-------------|-----------|------------|--------------|-----------|-------------|
| **Hispanic/Latino** | +850,755 | 18.3% | +28.6% | +164,197 | 77.2% | +49.5% |
| Eq. Hispanic/NonHispanic | +20,684 | 0.4% | +4.3% | +7,745 | 3.6% | +15.7% |
| Non-Hispanic | +1,767,713 | 38.0% | +2.9% | +32,005 | 15.0% | +0.6% |

Hispanic firms grew employment 28.6% vs. just 2.9% for Non-Hispanic.
Hispanic firms account for 77% of all net new employer firms.

### By Owner Sex

| Group | Net New Jobs | % of Total | Job Growth | Net New Firms | % of Total | Firm Growth |
|-------|-------------|-----------|------------|--------------|-----------|-------------|
| **Female-owned** | +1,537,356 | 33.0% | +15.1% | +215,580 | 101.3% | +18.9% |
| **Male-owned** | +2,167,149 | 46.6% | +4.8% | +141,734 | 66.6% | +4.1% |
| Equally male/female | -1,065,352 | -22.9% | -13.4% | -153,369 | -72.1% | -17.8% |

Female-owned firms created **33% of net new jobs** and **101% of net
new firms** (the "equally owned" category shrank). Female-owned firm
count grew 18.9% vs. 4.1% for male-owned.

### By Veteran Status

| Group | Net New Jobs | % of Total | Job Growth | Net New Firms | % of Total | Firm Growth |
|-------|-------------|-----------|------------|--------------|-----------|-------------|
| Veteran-owned | **-492,618** | -10.6% | **-12.8%** | **-76,604** | -36.0% | **-22.7%** |
| Eq. Veteran/NonVet | -295,302 | -6.3% | -20.9% | -48,021 | -22.6% | -32.9% |
| **Nonveteran-owned** | +3,427,073 | 73.7% | +5.9% | +328,567 | 154.4% | +6.6% |

Veteran-owned businesses are in **significant decline**: -22.7% of firms
and -12.8% of jobs lost since 2018. This reflects the aging veteran
population (Vietnam-era owners retiring/closing) outpacing new veteran
business formation.

### Summary: Who's Driving US Business Growth?

The groups with the strongest net positive contribution to US employer
firm growth (2018→2023), ranked by net new firms created:

| Rank | Group | Net New Firms | Firm Growth Rate |
|------|-------|--------------|-----------------|
| 1 | **Female-owned** | +215,580 | +18.9% |
| 2 | **Hispanic-owned** | +164,197 | +49.5% |
| 3 | **Male-owned** | +141,734 | +4.1% |
| 4 | **Asian-owned** | +107,081 | +18.5% |
| 5 | **Black-owned** | +76,334 | +61.3% |
| 6 | **AIAN-owned** | +30,685 | +125.6% |

The groups contracting:

| Group | Net New Firms | Firm Growth Rate |
|-------|--------------|-----------------|
| Nonminority-owned | -161,844 | -3.7% |
| Equally male/female | -153,369 | -17.8% |
| Veteran-owned | -76,604 | -22.7% |
| Eq. Veteran/NonVet | -48,021 | -32.9% |

Note: Race, ethnicity, and sex are **separate dimensions** in the ABS.
A firm can be both Hispanic *and* White-owned, or both Female-owned
*and* Asian-owned. The groups within each dimension sum to classifiable
totals but groups across dimensions overlap.

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

### GDP by Hispanic Origin Group (CLU/CERF Methodology Applied)

The [2025 US Latino GDP Report](https://blogs.callutheran.edu/cerf/files/2025/09/2025_USLatinoGDP_FINALrev.pdf)
by Cal Lutheran / UCLA estimates the total US Hispanic/Latino GDP at
**$4.06 trillion** in 2023 (14.6% of US GDP). Their methodology:

1. Start with BEA GDP decomposed across ~70 industry sectors
2. Compute Latino share of each sector's economic activity using ACS/CPS
   employment, income, and expenditure data
3. Sum: Latino GDP = Σ (Latino share of sector × Sector GDP)

We replicate this approach at the **origin-group level** by:
- Using BEA 2023 GDP by Industry (Value Added, nominal, 13 major sectors)
- Using ACS 2023 S0201 industry employment distribution by origin group
- Computing each group's labor-productivity-weighted GDP contribution
- Calibrating to the CLU aggregate of $4.06T

**Estimated GDP by Hispanic Origin Group (2023):**

| Origin Group | Est. GDP | % of Latino GDP | Workers | GDP/Worker |
|-------------|---------|----------------|---------|-----------|
| **Mexican** | **$2.29T** | **56.5%** | 18,024,005 | $127,196 |
| **Central American** | **$0.44T** | **10.8%** | 3,582,585 | $122,698 |
| **South American** | **$0.39T** | **9.5%** | 2,820,978 | $136,894 |
| **Puerto Rican** | **$0.36T** | **8.9%** | 2,616,196 | $137,379 |
| **Cuban** | **$0.18T** | **4.6%** | 1,320,588 | $140,055 |
| **Dominican** | **$0.15T** | **3.8%** | 1,148,039 | $132,993 |
| Other Hispanic | $0.24T | 6.0% | — | — |
| **Total Hispanic/Latino** | **$4.06T** | **100%** | 31,302,826 | $129,701 |

**Detail within Central American:**

| Subgroup | Est. GDP | % of Latino | Workers | GDP/Worker |
|----------|---------|-------------|---------|-----------|
| Salvadoran | $0.17T | 4.2% | 1,376,905 | $124,509 |
| Guatemalan | $0.12T | 3.0% | 1,023,643 | $117,651 |

**Detail within South American:**

| Subgroup | Est. GDP | % of Latino | Workers | GDP/Worker |
|----------|---------|-------------|---------|-----------|
| Colombian | $0.13T | 3.1% | 905,367 | $140,075 |

**Country equivalents:** The Mexican-American GDP alone ($2.29T) would
rank as the world's 10th largest economy — larger than Brazil, Canada,
or Russia. The Central American-American GDP ($0.44T) exceeds
the Philippines. The Puerto Rican-American GDP ($0.36T) exceeds Israel.

**GDP per worker varies by industry mix:**

| Group | GDP/Worker | Ratio to US Avg | Why |
|-------|-----------|----------------|-----|
| Cuban | $140,055 | 0.83x | More finance, professional svcs, transport |
| Colombian | $140,075 | 0.83x | More professional services, finance |
| Puerto Rican | $137,379 | 0.81x | More education/health, public admin |
| South American | $136,894 | 0.81x | Balanced mix; more professional svcs |
| Dominican | $132,993 | 0.79x | More transport, education/health |
| Mexican | $127,196 | 0.75x | More construction, agriculture, food svcs |
| Salvadoran | $124,509 | 0.74x | Heavy construction, food services |
| Central American | $122,698 | 0.73x | 18.6% in construction (highest of any group) |
| Guatemalan | $117,651 | 0.70x | 20.4% in construction, low finance/info |

Groups concentrated in higher-productivity sectors (finance, information,
professional services) generate more GDP per worker. Groups concentrated
in construction, agriculture, and food services have lower GDP per worker
despite strong labor force participation. This is an industry-mix effect,
not a worker quality effect.

**Key methodological caveats:**
- This uses labor-share allocation only; the CLU report also incorporates
  expenditure-side data (consumption, housing, investment)
- Within-industry wage differentials mean pure employment-share
  overestimates GDP; we calibrate to the CLU total to account for this
- Sub-group estimates assume the calibration factor (0.84) is uniform
  across origin groups; in reality, within-industry wage gaps may vary
- Origin categories overlap slightly (some individuals report multiple
  origins), so subgroups sum to slightly more than the total

**Data sources:**
- BEA GDP by Industry, Table TVA105-A (Value Added, nominal, 2023)
- ACS 2023 1-Year, Table S0201 (Selected Population Profile), variables
  S0201_194E through S0201_207E, by POPGROUP
- CLU/CERF 2025 US Latino GDP Report for calibration total

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

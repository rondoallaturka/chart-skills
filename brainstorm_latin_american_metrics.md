# Census Metrics Brainstorm: Latin American Groups in the US

Metrics available through the Census Bureau API for Latin American origin
groups, using the Selected Population Profiles (SPP) endpoint with POPGROUP
codes and the standard ACS detailed/subject tables.

## Target Population Groups (POPGROUP codes)

| Code | Group |
|------|-------|
| `400` | Hispanic or Latino (of any race) |
| `4015` | Mexican |
| `4038` | Puerto Rican |
| `4036` | Cuban |
| `4037` | Dominican |
| `4025` | Argentinean |
| `4028` | Colombian |
| `4033` | Venezuelan |
| `519` | Brazilian |

## Already Pulled

- Median household income by origin group
- % with bachelor's degree or higher
- Most-Mexican zip code per state
- Total US population baseline

---

## Metric Ideas by Category

### 1. Employment & Labor Force

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| Unemployment rate over time | COVID recovery differed by group; newer arrivals face different labor markets | S0201 employment vars, S2301_C04_001E |
| Labor force participation rate | Captures who's in the market at all, not just who's jobless | S0201 labor force vars |
| Industry of employment | Construction, agriculture, healthcare, hospitality patterns differ by origin | B24030 series (Hispanic cross-tabs) |
| Self-employment rate | Cubans historically high; how do Venezuelans compare? | S0201 self-employment vars |
| Occupation type | Management/professional vs. service vs. production by group | B24010 series |
| Mean commute time | Proxy for where people live relative to jobs | S0201 commute vars, B08303 |

### 2. Income & Wealth

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| Income distribution brackets | Full shape, not just median — % earning <$25K vs >$100K | B19001 series (Hispanic suffix I) |
| Per capita income | Controls for household size differences across groups | S0201 per capita income var |
| Poverty rate by origin | Especially children vs. elderly within each group | S0201 poverty vars, S1701 |
| Public assistance rates | SNAP, SSI, cash assistance by origin | B19058, B09010 |
| Earnings by sex | Gender pay gap within each origin group | S0201 earnings vars |

### 3. Housing & Geography

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| Homeownership rate | Cubans in Miami vs. Mexicans in TX vs. Puerto Ricans in NE | S0201 tenure vars |
| Rent burden (>30% of income) | Critical for newer immigrant groups facing high housing costs | B25070 (Hispanic cross-tabs) |
| Median home value by group | Wealth proxy; reflects where each group concentrates | S0201 home value vars |
| Geographic concentration by metro | Which MSAs have largest populations of each group? | B03001 by metro area |
| Overcrowding (persons per room) | Housing quality indicator that varies by group | B25014 |

### 4. Education

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| Full educational attainment ladder | Not just bachelor's — show <HS through graduate degree | S0201 education vars (multiple) |
| School enrollment (ages 18-24) | Are young adults pursuing higher ed? Varies by group | S0201 enrollment vars |
| Field of degree | Among bachelor's holders: STEM vs. business vs. education | B15012 series |
| Educational attainment by generation | Foreign-born vs. native-born within same origin | Cross-tab S0201 with nativity |

### 5. Language & Integration

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| English proficiency | % "very well" vs. "not at all" — established vs. newer groups | S0201 language vars |
| Language spoken at home | Spanish only vs. English only vs. bilingual | B16001, C16001 |
| Citizenship status | Naturalized vs. non-citizen vs. born citizen by origin | S0201 citizenship vars |
| Year of entry to US | Venezuelan wave post-2017; Mexican immigration peaked earlier | S0201 year of entry vars |
| Nativity (foreign-born %) | Some groups are majority US-born (Mexican, PR), others not | S0201 nativity vars |

### 6. Family & Household Structure

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| Average household size | Latin American households tend larger; varies by origin | S0201 household size vars |
| Single-parent household rate | Significant variance across groups | S0201 family type vars |
| Multigenerational households | Extended family living arrangements | B11017 |
| Married-couple family % | Family structure differs by group and generation | S0201 marital status vars |

### 7. Health & Insurance

| Metric | Why it's interesting | Likely variables |
|--------|---------------------|-----------------|
| Uninsured rate | Differs by citizenship status and state Medicaid policy | S0201 insurance vars |
| Insurance type | Employer vs. Medicaid vs. marketplace by origin | S2701 series |
| Disability rate | By age and origin group | S0201 disability vars |

---

## Time Series Ideas (strongest chart potential)

These metrics work well as line charts across ACS 1-Year data (2005-2024,
excluding 2020):

1. **Employment/unemployment rate by origin group** (2015-2024) — COVID dip
   and recovery, with each group as a line
2. **Median household income trajectory** (2010-2024) — which groups are
   gaining ground?
3. **Educational attainment (% bachelor's+)** over a decade — generational
   progress
4. **Homeownership rate** (2010-2024) — post-recession recovery, divergence
5. **Uninsured rate** (2010-2024) — ACA impact by origin group
6. **Venezuelan population growth** — barely registered pre-2017, now
   significant in several states
7. **English proficiency trends** for newer arrival groups
8. **Poverty rate** (2015-2024) — pre/post COVID, inflation impact

## Comparison Chart Ideas (side-by-side bar or grouped)

1. **8-group comparison for a single year**: Pick 5-6 key metrics and show
   all origin groups side by side (income, education, homeownership,
   uninsured rate, English proficiency, poverty)
2. **Origin group vs. national average**: How does each group compare to the
   US total population on the same metrics?
3. **State-level variation within a group**: e.g., Mexican median income in
   CA vs. TX vs. IL vs. AZ
4. **Generation gap**: Foreign-born vs. US-born within same origin group on
   education, income, English proficiency

## Data Feasibility Notes

- **SPP endpoint** (`/acs/acs1/spp`): Best for origin-group breakdowns but
  only covers areas with 65,000+ population. National and state-level are
  reliable. County/metro may have data gaps for smaller groups.
- **ACS 1-Year time series**: Available 2005-2024 (no 2020 due to COVID
  collection issues). Good for large geographies.
- **ACS 5-Year**: Available 2009-2023. Covers all geographies but
  represents a 5-year average, not a point-in-time snapshot. Less ideal for
  sharp time series but necessary for small-area analysis.
- **Hispanic cross-tabulations in B-tables**: Many detailed tables have
  suffix `I` for "Hispanic or Latino" (e.g., `B19013I_001E` = median
  household income for Hispanic households). These don't break down by
  origin group but are available at finer geographies.
- **POPGROUP codes**: Always verify with the discovery endpoint — codes have
  changed in the past and may change again.

# Estimating the GDP of the US Latino/Hispanic + Brazilian Population

Using Census Bureau data to approximate the economic output of the combined
Hispanic/Latino and Brazilian population in the United States.

## Why This Works (and Its Limits)

GDP is an output measure published by the Bureau of Economic Analysis, not a
Census variable. The Census doesn't directly measure GDP by ethnicity. But
the Census does measure **aggregate personal income** and **per capita income**
by population group, and personal income is the largest component of GDP.

By computing this population's share of total US personal income and applying
that ratio to GDP, we get a reasonable proxy for their share of economic
output. This assumes the income-to-output ratio is roughly uniform across
groups — a simplification, but a standard one used in similar analyses.

## Data Sources

All Census data: **2023 American Community Survey** (ACS 5-Year and 1-Year
Selected Population Profiles). GDP figure: **Bureau of Economic Analysis,
2023 annual estimate ($27.36 trillion).**

## Key Inputs

### Aggregate Personal Income (B19313, ACS 5-Year 2023)

| Population | Aggregate Income | Variable |
|------------|-----------------|----------|
| **Total US** | $14,388,718,351,400 | B19313_001E |
| **Hispanic/Latino** | $1,745,791,757,900 | B19313I_001E |

### Per Capita Income and Population (ACS 2023)

| Group | Population | Per Capita Income | Source |
|-------|-----------|-------------------|--------|
| **Total US** | ~334.9M | $43,289 | B19301_001E (ACS5) |
| **Hispanic/Latino** | 65,140,277 | $28,026 | S0201_235E, POPGROUP=400 (SPP) |
| **Brazilian** | 609,838 | $35,575 | S0201_235E, POPGROUP=519 (SPP) |

### US GDP (BEA)

| Year | Nominal GDP |
|------|------------|
| 2023 | $27,360,000,000,000 |

**Note:** Brazilians are classified separately from Hispanic/Latino in the
Census. "Hispanic or Latino" refers to Spanish-speaking origin; Brazilians
(Portuguese-speaking) are excluded. This is why we add them explicitly.

## Estimation Methods

### Method A: Income Share → GDP Share

The most direct approach. Hispanic/Latino aggregate personal income is
reported directly by the Census. For Brazilians, we estimate aggregate
income from population × per capita income.

```
Hispanic aggregate personal income:        $1,745,791,757,900
Brazilian estimated aggregate income:
  609,838 × $35,575 =                        $21,695,087,450
                                           ─────────────────
Combined:                                  $1,767,486,845,350

Share of US total personal income:
  $1,767.5B / $14,388.7B =                           12.28%

Estimated GDP contribution:
  12.28% × $27,360,000,000,000 =           $3,359,808,000,000
                                           ≈ $3.36 trillion
```

### Method B: Per Capita Income Ratio × Per Capita GDP

An alternative that scales each group's per capita GDP by their income
ratio relative to the national average.

```
US per capita GDP:
  $27.36T / 334.9M =                              $81,697

Hispanic income ratio:
  $28,026 / $43,289 =                              0.6474
Hispanic per capita GDP proxy:
  0.6474 × $81,697 =                              $52,907
Hispanic GDP:
  65,140,277 × $52,907 =                  $3,446,345,000,000

Brazilian income ratio:
  $35,575 / $43,289 =                              0.8218
Brazilian per capita GDP proxy:
  0.8218 × $81,697 =                              $67,138
Brazilian GDP:
  609,838 × $67,138 =                        $40,940,000,000

Combined:                                  $3,487,285,000,000
                                           ≈ $3.49 trillion
```

## Result

| Method | Estimated GDP |
|--------|--------------|
| A (income share) | **$3.36 trillion** |
| B (per capita ratio) | **$3.49 trillion** |
| **Midpoint** | **~$3.4 trillion** |

## Global Context

If the US Latino/Hispanic + Brazilian population were a standalone economy,
its ~$3.4 trillion GDP would rank approximately **5th–6th in the world**
(2023 figures):

| Rank | Country | GDP (2023, nominal) |
|------|---------|-------------------|
| 1 | United States | $27.4T |
| 2 | China | $17.8T |
| 3 | Germany | $4.5T |
| 4 | Japan | $4.2T |
| 5 | India | $3.7T |
| **→** | **US Latino + Brazilian pop.** | **~$3.4T** |
| 6 | United Kingdom | $3.3T |
| 7 | France | $3.0T |

## Caveats

1. **This is a proportional estimate, not a true GDP accounting.** GDP
   includes corporate profits, government spending, capital income, and net
   exports — not just personal income. The approach assumes each group's
   share of personal income approximates their share of GDP.

2. **The income-share method may understate GDP contribution.** If Latino
   workers are disproportionately in industries with high output-per-worker
   relative to wages (e.g., agriculture, construction), their GDP
   contribution could exceed their income share.

3. **Brazilian population may be undercounted.** Census estimates for
   smaller immigrant populations often miss unauthorized residents and
   recent arrivals.

4. **No double-counting risk.** Census definitions are clear: POPGROUP 400
   (Hispanic/Latino) and POPGROUP 519 (Brazilian) are mutually exclusive
   categories.

5. **Single-year snapshot.** Both Census income data and BEA GDP are for
   2023, so the year alignment is good. A time series would require pulling
   both data sources across multiple years.

## Reproducibility

All data can be fetched with the census_fetch.py script:

```bash
# Aggregate personal income (total + Hispanic)
python scripts/census_fetch.py fetch 2023 acs5 "NAME,B19313_001E,B19313I_001E" "us:1"

# Per capita income and population — Hispanic/Latino
python scripts/census_fetch.py fetch 2023 acs1_spp "NAME,S0201_001E,S0201_235E" "us:1" \
  --param POPGROUP=400

# Per capita income and population — Brazilian
python scripts/census_fetch.py fetch 2023 acs1_spp "NAME,S0201_001E,S0201_235E" "us:1" \
  --param POPGROUP=519
```

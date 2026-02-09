---
name: latam-earnings
description: Fetch earnings reports and financial statements for Latin American companies from SEC EDGAR and CVM Brazil
version: 0.1.0
author: chart-skills
tags: [earnings, latin-america, financial-statements, sec, cvm, brazil, mexico, chile, colombia, argentina]
---

# Latin American Earnings Fetcher

Fetch earnings reports and financial statements for Latin American companies. Supports two primary data sources:

1. **SEC EDGAR** — For US-listed LatAm companies (ADRs/direct listings) via 20-F and 6-K filings
2. **CVM Brazil** — For B3-listed companies via DFP (annual) and ITR (quarterly) filings

## Usage

```
/latam-earnings <company name, ticker, or query>
```

### Examples

```
/latam-earnings Petrobras latest earnings
/latam-earnings Vale annual report 2024
/latam-earnings MELI quarterly results
/latam-earnings Brazilian banks earnings comparison
/latam-earnings Cemex 20-F filing
/latam-earnings WEG quarterly results from CVM
```

## Instructions

When the user invokes this skill, determine:
1. **Which company/companies** they want
2. **Which source** is appropriate (SEC for US-listed, CVM for Brazil-only)
3. **What time period** (latest, specific year/quarter, or range)

Then follow the source-specific workflow below.

---

## Source 1: SEC EDGAR (US-Listed LatAm Companies)

Use this for any Latin American company that trades on NYSE or NASDAQ. These companies file **20-F** (annual) and **6-K** (quarterly/event) forms.

### Step 1: Identify the company's CIK number

Use the EDGAR company search to find the CIK:

```python
import requests

def search_edgar_company(query):
    """Search EDGAR for a company by name or ticker."""
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {"q": query, "dateRange": "custom", "forms": "20-F,6-K"}
    headers = {"User-Agent": "LatAmEarnings research@example.com"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    return r.json()
```

Alternatively, use the company tickers endpoint:
```
https://www.sec.gov/files/company_tickers.json
```

**Known CIKs for major LatAm companies:**

| Company | Ticker | CIK | Country |
|---------|--------|-----|---------|
| Petrobras | PBR | 1119639 | Brazil |
| Vale | VALE | 917851 | Brazil |
| Nu Holdings | NU | 1854401 | Brazil |
| Ambev | ABEV | 1290677 | Brazil |
| Itau Unibanco | ITUB | 1132260 | Brazil |
| Bradesco | BBD | 1160330 | Brazil |
| Mercado Libre | MELI | 1099590 | Argentina |
| Globant | GLOB | 1557860 | Argentina |
| America Movil | AMX | 1129137 | Mexico |
| Cemex | CX | 1076378 | Mexico |
| Fomento Economico | FMX | 806592 | Mexico |
| Ecopetrol | EC | 1444406 | Colombia |
| Credicorp | BAP | 1001290 | Peru |
| SQM | SQM | 1060349 | Chile |
| Copa Holdings | CPA | 1345105 | Panama |

### Step 2: Fetch the filing history

```python
def get_edgar_filings(cik, form_type="20-F"):
    """Get filing history for a company from EDGAR."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    headers = {"User-Agent": "LatAmEarnings research@example.com"}
    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()

    # Extract recent filings
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    filings = []
    for i, form in enumerate(forms):
        if form == form_type:
            filings.append({
                "form": form,
                "date": dates[i],
                "accession": accessions[i],
                "document": primary_docs[i],
            })
    return filings, data.get("name", ""), data.get("tickers", [])
```

### Step 3: Fetch XBRL financial data

For structured financial data, use the Company Facts API:

```python
def get_company_financials(cik):
    """Get all XBRL financial facts for a company."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    headers = {"User-Agent": "LatAmEarnings research@example.com"}
    r = requests.get(url, headers=headers, timeout=15)
    return r.json()
```

**Important**: Most LatAm filers use the `ifrs-full` taxonomy, not `us-gaap`. Key IFRS tags:

| Tag | Description |
|-----|-------------|
| `Revenue` | Total revenue |
| `ProfitLoss` | Net income |
| `ProfitLossAttributableToOwnersOfParent` | Net income to equity holders |
| `BasicEarningsLossPerShare` | EPS |
| `Assets` | Total assets |
| `Equity` | Total equity |
| `CashAndCashEquivalents` | Cash position |
| `Liabilities` | Total liabilities |
| `GrossProfit` | Gross profit |
| `OperatingExpense` | Operating expenses |

To query a specific concept:
```python
def get_company_concept(cik, taxonomy, tag):
    """Get a specific financial metric across all filings."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{tag}.json"
    headers = {"User-Agent": "LatAmEarnings research@example.com"}
    r = requests.get(url, headers=headers, timeout=15)
    return r.json()

# Example: Get Petrobras revenue history
data = get_company_concept(1119639, "ifrs-full", "Revenue")
```

### Step 4: Download the actual filing document

If the user wants the full filing (not just XBRL data):

```python
def get_filing_url(cik, accession, document):
    """Construct URL for the actual filing document."""
    cik_padded = str(cik).zfill(10)
    accession_clean = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{accession_clean}/{document}"
```

The filing can then be processed with the `/pdf-to-llm` skill if it's a PDF, or read directly if HTML.

### SEC EDGAR Pitfalls

1. **Must include User-Agent header** — SEC blocks requests without it. Use format: `"CompanyName email@example.com"`
2. **10 requests/second rate limit** — Add `time.sleep(0.1)` between requests
3. **IFRS vs US-GAAP** — Try `ifrs-full` first for LatAm filers; fall back to `us-gaap`
4. **CIK zero-padding** — CIKs must be zero-padded to 10 digits in URLs
5. **20-F annual timing** — Filed within 4 months of fiscal year end (April for Dec year-end)
6. **6-K variability** — 6-K can contain quarterly earnings, press releases, or other material events. Filter by date and inspect content.

---

## Source 2: CVM Brazil (B3-Listed Companies)

Use this for Brazilian companies listed on B3, whether or not they also have ADRs. This is especially useful for companies without US listings.

### Step 1: Download the company registry

```python
import pandas as pd
import requests
import zipfile
import io

def get_cvm_companies():
    """Download the CVM company registry."""
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    df = pd.read_csv(url, sep=";", encoding="latin-1")
    # Filter to active companies
    active = df[df["SIT"] == "ATIVO"]
    return active[["CNPJ_CIA", "DENOM_CIA", "DENOM_COMERC", "CD_CVM", "SETOR_ATIV"]]
```

### Step 2: Download financial statements

```python
def get_cvm_financials(year, report_type="dfp"):
    """
    Download CVM financial data for a given year.
    report_type: 'dfp' (annual) or 'itr' (quarterly)
    """
    base = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC"
    url = f"{base}/{report_type.upper()}/DADOS/{report_type}_cia_aberta_{year}.zip"
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    dataframes = {}
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for filename in z.namelist():
            if filename.endswith(".csv"):
                with z.open(filename) as f:
                    df = pd.read_csv(f, sep=";", encoding="latin-1")
                    # Key: short name like 'BPA', 'DRE', etc.
                    key = filename.split("_")[0] if "_" in filename else filename.replace(".csv", "")
                    dataframes[key] = df
    return dataframes
```

### Step 3: Filter for a specific company

```python
def filter_company(dataframes, company_name=None, cnpj=None, cd_cvm=None):
    """Filter CVM data for a specific company."""
    results = {}
    for key, df in dataframes.items():
        if cnpj and "CNPJ_CIA" in df.columns:
            filtered = df[df["CNPJ_CIA"] == cnpj]
        elif cd_cvm and "CD_CVM" in df.columns:
            filtered = df[df["CD_CVM"] == cd_cvm]
        elif company_name and "DENOM_CIA" in df.columns:
            filtered = df[df["DENOM_CIA"].str.contains(company_name, case=False, na=False)]
        else:
            continue
        if not filtered.empty:
            results[key] = filtered
    return results
```

### Step 4: Interpret the data

CVM CSVs use a hierarchical account code system:

| Account Code Prefix | Statement | Key Items |
|---------------------|-----------|-----------|
| `1.*` | Balance Sheet — Assets | `1` Total Assets, `1.01` Current Assets, `1.02` Non-current |
| `2.*` | Balance Sheet — Liabilities | `2` Total Liabilities + Equity, `2.01` Current, `2.03` Equity |
| `3.*` | Income Statement (DRE) | `3.01` Revenue, `3.05` EBIT, `3.11` Net Income |
| `4.*` | Comprehensive Income | |
| `5.*` | Changes in Equity | |
| `6.*` | Cash Flow Statement | `6.01` Operating, `6.02` Investing, `6.03` Financing |
| `7.*` | Value Added Statement | |

**Key columns**:
- `CD_CONTA`: Account code (hierarchical, e.g., `3.01`)
- `DS_CONTA`: Account description (in Portuguese)
- `VL_CONTA`: Value (in BRL thousands, typically)
- `DT_REFER`: Reference date
- `DT_INI_EXERC` / `DT_FIM_EXERC`: Period start/end dates
- `ORDEM_EXERC`: `ULTIMO` (current period) or `PENULTIMO` (prior period for comparison)
- `VERSAO`: Filing version (use highest number = latest amendment)

### CVM Pitfalls

1. **Encoding is latin-1** — Must specify `encoding="latin-1"` when reading CSVs
2. **Separator is semicolon** — Use `sep=";"` in pandas
3. **Values in BRL** — No currency conversion; note in output
4. **Multiple versions** — Same company may have multiple filings (amendments). Use the highest `VERSAO` number.
5. **Portuguese labels** — Account descriptions are in Portuguese. Use `CD_CONTA` for programmatic matching.
6. **Consolidated vs Individual** — Files contain both. Filter by the filename suffix (e.g., `con` for consolidated, `ind` for individual) or by `ESCALA_MOEDA` field.
7. **Historical range** — DFP available 2010-present; ITR 2011-present.
8. **Accented field values** — `ORDEM_EXERC` uses `ÚLTIMO` (with accent), not `ULTIMO`. Match on `LTIMO` substring or normalize Unicode.

---

## Workflow Decision Tree

```
User requests earnings data
  |
  v
Is the company US-listed (ADR/direct)?
  |
  +-- YES --> Use SEC EDGAR (Source 1)
  |             |
  |             +-- Need structured numbers? --> Company Facts / Concept API (XBRL)
  |             +-- Need full document? --> Download 20-F/6-K filing
  |
  +-- NO --> Is the company Brazilian?
              |
              +-- YES --> Use CVM (Source 2)
              |             |
              |             +-- Annual data? --> DFP
              |             +-- Quarterly data? --> ITR
              |
              +-- NO --> Check if company has US-listed securities
                          |
                          +-- If yes --> SEC EDGAR
                          +-- If no --> Note limited programmatic access;
                                        suggest checking issuer IR page directly
```

## Output Format

Always save results as CSV and/or JSON in the `output/` directory:

```python
# Save earnings summary
import csv
import json

def save_results(data, company_name, format="both"):
    """Save earnings data to output/ directory."""
    safe_name = company_name.lower().replace(" ", "_")

    if format in ("csv", "both"):
        with open(f"output/{safe_name}_earnings.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    if format in ("json", "both"):
        with open(f"output/{safe_name}_earnings.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
```

## Portuguese-English Account Label Reference

| Portuguese (DS_CONTA) | English | CD_CONTA |
|------------------------|---------|----------|
| Receita de Venda de Bens e/ou Servicos | Revenue | 3.01 |
| Custo dos Bens e/ou Servicos Vendidos | Cost of Goods Sold | 3.02 |
| Resultado Bruto | Gross Profit | 3.03 |
| Despesas/Receitas Operacionais | Operating Expenses/Income | 3.04 |
| Resultado Antes do Resultado Financeiro e dos Tributos | EBIT | 3.05 |
| Resultado Financeiro | Financial Result | 3.06 |
| Resultado Antes dos Tributos sobre o Lucro | EBT | 3.07 |
| Lucro/Prejuizo Consolidado do Periodo | Net Income (Consolidated) | 3.11 |
| Lucro por Acao - Basico | Basic EPS | 3.99.01.01 |
| Ativo Total | Total Assets | 1 |
| Passivo Total | Total Liabilities | 2 |
| Patrimonio Liquido Consolidado | Shareholders' Equity | 2.03 |
| Caixa e Equivalentes de Caixa | Cash and Equivalents | 6.05.01 |

## Combining Sources

For companies with both US and Brazilian listings (e.g., Petrobras, Vale, Itau), you can cross-reference:
- SEC EDGAR XBRL data (in USD) for investor-facing metrics
- CVM data (in BRL) for detailed Brazilian-standard breakdowns

This is useful for reconciliation, currency analysis, or getting more granular line items than what's in the 20-F.

# Latin American Earnings Reports: Research & Data Source Inventory

## Problem Statement

Finding earnings reports for Latin American companies is fragmented across multiple systems:
- US-listed companies (ADRs and direct listings) file with the SEC
- Brazilian companies file with CVM
- Mexican companies file with CNBV via BMV
- Chilean companies file with CMF
- Colombian companies file with Superfinanciera
- Argentine companies file with CNV via BYMA

There is no single unified API. Each country has different data formats, filing conventions, and levels of programmatic accessibility.

---

## Tier 1: Best Programmatic Access (Free, Structured Data)

### 1. SEC EDGAR (US-listed LatAm companies)

**What it covers**: Any Latin American company with ADRs or direct listings on NYSE/NASDAQ. This includes major names like Petrobras, Vale, Mercado Libre, Grupo Bimbo, America Movil, Nu Holdings, etc.

**Filing types**:
- **20-F**: Annual report for foreign private issuers (equivalent to 10-K)
- **6-K**: Current report for foreign private issuers (equivalent to 8-K; often contains quarterly earnings)

**APIs (free, no auth required)**:
| API | Endpoint | Use |
|-----|----------|-----|
| Submissions | `https://data.sec.gov/submissions/CIK{cik}.json` | Filing history, metadata, ticker/exchange |
| Company Facts (XBRL) | `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | All structured financial data |
| Company Concept | `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json` | Single metric across all filings |
| Frames | `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/CY{year}.json` | Cross-company comparison for one metric |
| Full-Text Search | `https://efts.sec.gov/LATEST/search-index?q={query}&forms=20-F,6-K` | Search filing content |

**Key detail**: Foreign issuers often use `ifrs-full` taxonomy (not `us-gaap`). When querying Company Concept, use `ifrs-full` for most LatAm filers.

**Rate limit**: 10 requests/second. Must include `User-Agent` header with contact email.

**Python packages**:
- `sec-edgar-api` (free, wraps official API)
- `sec-api` (commercial, more powerful search)

### 2. CVM Dados Abertos (Brazil)

**What it covers**: All publicly traded companies on B3 (Brasil, Bolsa, Balcao) — ~400+ companies.

**Filing types**:
- **DFP** (Demonstracoes Financeiras Padronizadas): Annual standardized financial statements
- **ITR** (Informacoes Trimestrais): Quarterly financial information

**Data access** (free, no auth):
| Resource | URL Pattern | Format |
|----------|-------------|--------|
| DFP annual data | `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip` | ZIP of CSVs |
| ITR quarterly data | `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{year}.zip` | ZIP of CSVs |
| Company registry | `https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv` | CSV |
| Dataset catalog | `https://dados.cvm.gov.br/dataset/` | HTML/API |

**CSV contents per ZIP** (semicolon-delimited, latin-1 encoding):
- `BPA_*` — Balance Sheet Assets
- `BPP_*` — Balance Sheet Liabilities
- `DRE_*` — Income Statement
- `DRA_*` — Comprehensive Income
- `DFC_*` — Cash Flow Statement
- `DVA_*` — Value Added Statement
- `DMPL_*` — Changes in Equity

**Historical coverage**: 2010 to present (DFP); 2011 to present (ITR).

This is the **best local-exchange data source** — structured CSV, free, well-organized, complete coverage.

---

## Tier 2: Partial Programmatic Access (APIs exist but limited)

### 3. BMV / CNBV (Mexico)

**What it covers**: Companies listed on Bolsa Mexicana de Valores (~140 issuers).

**Access methods**:
- BMV Web Services: Commercial API for issuer information. Details at `bmv.com.mx/en/information-products/web-services`. Requires contacting BMV for pricing/access.
- CNBV filings: Available through BMV issuer pages (e.g., `bmv.com.mx/en/issuers/financialinformation/{issuer}`). No public REST API — web scraping would be required.
- Individual issuer IR pages often host CNBV filings directly (e.g., PEMEX at `pemex.com/en/investors/regulatory-filings`).

**Feasibility**: Medium. The BMV site uses CAPTCHAs. Best approach is scraping individual issuer IR pages or using BMV's commercial web services.

### 4. BYMA / CNV (Argentina)

**What it covers**: Companies listed on Bolsas y Mercados Argentinos.

**Access methods**:
- BYMA APIs: Official market data APIs at `byma.com.ar/en/byma-apis`. Focused on real-time trading data, not earnings filings.
- CNV website (`cnv.gob.ar`): Regulatory filings portal. No public developer API found.
- Third-party: EODHD provides fundamental data for BYMA-listed stocks including EPS.

**Feasibility**: Low-Medium. No direct free API for earnings filings. Would require web scraping CNV or using paid third-party data.

### 5. Bolsa de Santiago / CMF (Chile)

**What it covers**: Companies listed on Bolsa de Comercio de Santiago.

**Access methods**:
- CMF portal (`cmfchile.cl`): Financial statements in PDF and XBRL for supervised entities. Structured URLs but no REST API.
- Bolsa de Santiago API: Market data API (requires API key request). Python SDK at `github.com/LautaroParada/bolsa-santiago`. Focused on trading data, not filings.

**Feasibility**: Low-Medium. CMF has structured data but requires scraping. XBRL filings are a plus for machine readability.

### 6. BVC / Superfinanciera (Colombia)

**What it covers**: Companies listed on Bolsa de Valores de Colombia.

**Access methods**:
- Superfinanciera (`superfinanciera.gov.co`): Financial statements and PowerBI dashboards. No public REST API.
- SIIS portal (`siis.ia.supersociedades.gov.co`): Financial/legal data for companies reporting to Supersociedades.
- BVC market data: Available at `bvc.com.co/market-data-and-electronic-access`.

**Feasibility**: Low. PowerBI dashboards and PDF-only filings. Requires scraping or manual download.

---

## Tier 3: Aggregator APIs (Paid, but broad coverage)

### 7. Financial Modeling Prep (FMP)

- Earnings Calendar, financial statements, earnings transcripts for 8,000+ companies
- Coverage: Primarily US-listed; international companies with US presence
- Free tier: 250 requests/day, limited to US data
- Paid tiers: Broader international coverage
- Endpoint: `https://financialmodelingprep.com/api/v3/earning_calendar`

### 8. Finnhub

- Earnings calendar with global coverage
- Free tier available with rate limits
- Endpoint: `https://finnhub.io/api/v1/calendar/earnings`

### 9. Twelve Data

- Coverage includes BVC (Colombia), and potentially other LatAm exchanges
- Analyst projections, EOD data, dividend calendars
- Paid plans for full access

### 10. EODHD (End of Day Historical Data)

- Covers BYMA (Argentina), and other exchanges
- Fundamental data including EPS
- API access in JSON/CSV

---

## Recommended Strategy: Three-Layer Approach

### Layer 1: SEC EDGAR (highest priority)
For any LatAm company with US listings. This captures the largest, most investable companies — the ones most users care about. Free, well-structured, real-time.

### Layer 2: CVM Brazil (second priority)
Brazil is the largest LatAm market. CVM's open data portal is remarkably good — structured CSVs, free, complete. This covers companies that may not have ADRs.

### Layer 3: Country-specific scraping + aggregators (future expansion)
For Mexico, Chile, Colombia, Argentina — use a combination of:
- Scraping issuer IR pages (most reliable for individual companies)
- CMF XBRL data (Chile)
- Paid aggregator APIs for broad coverage

---

## Company Universe: Major LatAm Companies by Source

### US-Listed (SEC EDGAR — 20-F/6-K filers)

| Company | Country | Ticker | CIK | Sector |
|---------|---------|--------|-----|--------|
| Petrobras | Brazil | PBR | 1119639 | Energy |
| Vale | Brazil | VALE | 917851 | Mining |
| Nu Holdings | Brazil | NU | 1854401 | Fintech |
| Ambev | Brazil | ABEV | 1290677 | Beverages |
| Itau Unibanco | Brazil | ITUB | 1132260 | Banking |
| Bradesco | Brazil | BBD | 1160330 | Banking |
| Banco Santander Brasil | Brazil | BSBR | 1427437 | Banking |
| Mercado Libre | Argentina | MELI | 1099590 | E-commerce |
| Globant | Argentina | GLOB | 1557860 | Technology |
| Despegar | Argentina | DESP | 1701985 | Travel |
| Grupo Bimbo | Mexico | BIMBOA | — | Consumer |
| America Movil | Mexico | AMX | 1129137 | Telecom |
| Cemex | Mexico | CX | 1076378 | Materials |
| Grupo Televisa | Mexico | TV | 912892 | Media |
| Fomento Economico | Mexico | FMX | 806592 | Beverages |
| Copa Holdings | Panama | CPA | 1345105 | Airlines |
| Ecopetrol | Colombia | EC | 1444406 | Energy |
| Credicorp | Peru | BAP | 1001290 | Banking |
| SQM | Chile | SQM | 1060349 | Chemicals |
| LATAM Airlines | Chile | LTM | — | Airlines |
| Banco de Chile | Chile | BCH | 1161125 | Banking |

### B3-Only (CVM data)

Companies like Magazine Luiza (MGLU3), WEG (WEGE3), Localiza (RENT3), Raia Drogasil (RADL3), B3 itself (B3SA3), and hundreds more that don't have ADRs.

---

## Data Format Considerations

### SEC EDGAR XBRL
- Structured JSON via API
- Uses `ifrs-full` or `us-gaap` taxonomy
- Key tags: `Revenue`, `ProfitLoss`, `EarningsPerShare`, `Assets`, `Equity`
- Period-aware (instant vs duration facts)

### CVM CSV
- Semicolon-delimited, latin-1 encoding
- Columns: `CNPJ_CIA`, `DENOM_CIA`, `CD_CVM`, `DT_REFER`, `VERSAO`, `CD_CONTA`, `DS_CONTA`, `VL_CONTA`, `ST_CONTA_FIXA`
- Account codes follow a hierarchical structure (e.g., `1` = Assets, `2` = Liabilities, `3` = Income Statement)
- Values in BRL (Brazilian Reais)

---

## Key Challenges & Mitigations

1. **No single API covers everything** → Build a multi-source fetcher with source priority
2. **CIK lookup for SEC** → Use EDGAR company search or maintain a curated mapping
3. **IFRS vs US-GAAP taxonomy differences** → Support both, prefer `ifrs-full` for LatAm filers
4. **CVM data is in Portuguese** → Provide account code → English label mapping
5. **Rate limits** → Respect SEC's 10 req/s; batch CVM downloads
6. **Currency differences** → USD for SEC filings, BRL for CVM; note currency in output
7. **Filing lag** → SEC 20-F due 4 months after fiscal year end; CVM DFP due 3 months

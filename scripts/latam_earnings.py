#!/usr/bin/env python3
"""
Latin American Earnings Fetcher

Fetch earnings reports and financial statements for Latin American companies from:
1. SEC EDGAR — US-listed companies (ADRs/direct listings) via 20-F and 6-K filings
2. CVM Brazil — B3-listed companies via DFP (annual) and ITR (quarterly) filings

Usage:
    # SEC EDGAR: Search for a company
    python latam_earnings.py edgar search "Petrobras"

    # SEC EDGAR: Get filing history
    python latam_earnings.py edgar filings 1119639 --form 20-F

    # SEC EDGAR: Get XBRL financial data
    python latam_earnings.py edgar financials 1119639

    # SEC EDGAR: Get a specific metric
    python latam_earnings.py edgar concept 1119639 ifrs-full Revenue

    # CVM: List companies
    python latam_earnings.py cvm companies --search "Petrobras"

    # CVM: Download annual financial data
    python latam_earnings.py cvm dfp 2023 --company "PETROBRAS"

    # CVM: Download quarterly financial data
    python latam_earnings.py cvm itr 2023 --company "PETROBRAS"
"""

import argparse
import csv
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EDGAR_BASE = "https://data.sec.gov"
EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
EDGAR_TICKERS = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT = "LatAmEarnings research@example.com"

CVM_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
CVM_COMPANY_REG = f"{CVM_BASE}/CAD/DADOS/cad_cia_aberta.csv"

# Known CIKs for major LatAm companies
KNOWN_CIKS = {
    "PBR":  1119639,   # Petrobras (Brazil)
    "VALE": 917851,    # Vale (Brazil)
    "NU":   1854401,   # Nu Holdings (Brazil)
    "ABEV": 1290677,   # Ambev (Brazil)
    "ITUB": 1132260,   # Itau Unibanco (Brazil)
    "BBD":  1160330,   # Bradesco (Brazil)
    "BSBR": 1427437,   # Banco Santander Brasil (Brazil)
    "MELI": 1099590,   # Mercado Libre (Argentina)
    "GLOB": 1557860,   # Globant (Argentina)
    "AMX":  1129137,   # America Movil (Mexico)
    "CX":   1076378,   # Cemex (Mexico)
    "FMX":  806592,    # Fomento Economico Mexicano (Mexico)
    "TV":   912892,    # Grupo Televisa (Mexico)
    "EC":   1444406,   # Ecopetrol (Colombia)
    "BAP":  1001290,   # Credicorp (Peru)
    "SQM":  1060349,   # SQM (Chile)
    "CPA":  1345105,   # Copa Holdings (Panama)
    "BCH":  1161125,   # Banco de Chile (Chile)
}

# Portuguese to English account labels for CVM data
CVM_ACCOUNT_LABELS = {
    "3.01": "Revenue",
    "3.02": "Cost of Goods Sold",
    "3.03": "Gross Profit",
    "3.04": "Operating Expenses/Income",
    "3.05": "EBIT",
    "3.06": "Financial Result",
    "3.07": "EBT (Earnings Before Tax)",
    "3.11": "Net Income (Consolidated)",
    "3.99.01.01": "Basic EPS",
    "1": "Total Assets",
    "1.01": "Current Assets",
    "1.02": "Non-current Assets",
    "2": "Total Liabilities + Equity",
    "2.01": "Current Liabilities",
    "2.02": "Non-current Liabilities",
    "2.03": "Shareholders' Equity",
}


# ---------------------------------------------------------------------------
# SEC EDGAR functions
# ---------------------------------------------------------------------------

class EdgarClient:
    """Client for SEC EDGAR APIs."""

    def __init__(self, user_agent=USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last_request = 0

    def _throttle(self):
        """Respect SEC rate limit of 10 req/s."""
        elapsed = time.time() - self._last_request
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        self._last_request = time.time()

    def _get(self, url, params=None, timeout=15):
        self._throttle()
        r = self.session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def search_companies(self, query):
        """Search EDGAR for companies by name or ticker."""
        # Try the company tickers file first
        data = self._get(EDGAR_TICKERS)
        results = []
        query_lower = query.lower()
        for entry in data.values():
            name = entry.get("title", "").lower()
            ticker = entry.get("ticker", "").lower()
            if query_lower in name or query_lower in ticker:
                results.append({
                    "cik": entry["cik_str"],
                    "ticker": entry["ticker"],
                    "name": entry["title"],
                })
        return results

    def get_submissions(self, cik):
        """Get filing history for a company."""
        cik_padded = str(cik).zfill(10)
        return self._get(f"{EDGAR_BASE}/submissions/CIK{cik_padded}.json")

    def get_filings(self, cik, form_type="20-F", limit=10):
        """Get recent filings of a specific type."""
        data = self.get_submissions(cik)
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        filings = []
        for i, form in enumerate(forms):
            if form == form_type:
                cik_padded = str(cik).zfill(10)
                acc_clean = accessions[i].replace("-", "")
                doc_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik_padded}/{acc_clean}/{primary_docs[i]}"
                )
                filings.append({
                    "form": form,
                    "filing_date": dates[i],
                    "accession": accessions[i],
                    "document": primary_docs[i],
                    "description": descriptions[i] if i < len(descriptions) else "",
                    "url": doc_url,
                })
                if len(filings) >= limit:
                    break

        company_name = data.get("name", "")
        tickers = data.get("tickers", [])
        return filings, company_name, tickers

    def get_company_facts(self, cik):
        """Get all XBRL financial facts for a company."""
        cik_padded = str(cik).zfill(10)
        return self._get(f"{EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik_padded}.json")

    def get_company_concept(self, cik, taxonomy, tag):
        """Get a specific financial metric across all filings."""
        cik_padded = str(cik).zfill(10)
        url = f"{EDGAR_BASE}/api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{tag}.json"
        return self._get(url)

    def extract_key_financials(self, cik, taxonomy="ifrs-full"):
        """
        Extract key financial metrics from XBRL data.
        Tries ifrs-full first, falls back to us-gaap.
        """
        facts = self.get_company_facts(cik)
        all_facts = facts.get("facts", {})

        # Try the requested taxonomy, fall back to the other
        if taxonomy in all_facts:
            tax_facts = all_facts[taxonomy]
        elif "ifrs-full" in all_facts:
            taxonomy = "ifrs-full"
            tax_facts = all_facts["ifrs-full"]
        elif "us-gaap" in all_facts:
            taxonomy = "us-gaap"
            tax_facts = all_facts["us-gaap"]
        else:
            return {"error": "No XBRL data found", "available_taxonomies": list(all_facts.keys())}

        # Key metrics to extract
        key_tags = {
            "ifrs-full": [
                "Revenue", "ProfitLoss", "BasicEarningsLossPerShare",
                "Assets", "Equity", "Liabilities",
                "CashAndCashEquivalents", "GrossProfit",
            ],
            "us-gaap": [
                "Revenues", "NetIncomeLoss", "EarningsPerShareBasic",
                "Assets", "StockholdersEquity", "Liabilities",
                "CashAndCashEquivalentsAtCarryingValue", "GrossProfit",
            ],
        }

        tags = key_tags.get(taxonomy, key_tags["ifrs-full"])
        results = {"taxonomy": taxonomy, "company": facts.get("entityName", ""), "metrics": {}}

        for tag in tags:
            if tag in tax_facts:
                concept = tax_facts[tag]
                label = concept.get("label", tag)
                units = concept.get("units", {})
                # Get the most recent values
                for unit_name, unit_facts in units.items():
                    # Sort by end date descending
                    sorted_facts = sorted(
                        [f for f in unit_facts if "end" in f],
                        key=lambda x: x.get("end", ""),
                        reverse=True,
                    )
                    recent = sorted_facts[:8]  # Last 8 periods
                    results["metrics"][tag] = {
                        "label": label,
                        "unit": unit_name,
                        "recent_values": [
                            {
                                "value": f["val"],
                                "end": f.get("end", ""),
                                "start": f.get("start", ""),
                                "form": f.get("form", ""),
                                "filed": f.get("filed", ""),
                            }
                            for f in recent
                        ],
                    }

        return results


# ---------------------------------------------------------------------------
# CVM Brazil functions
# ---------------------------------------------------------------------------

class CvmClient:
    """Client for CVM Brazil open data."""

    def __init__(self):
        self.session = requests.Session()

    def get_companies(self, search=None):
        """Download and optionally filter the CVM company registry."""
        r = self.session.get(CVM_COMPANY_REG, timeout=30)
        r.raise_for_status()

        # Parse CSV (semicolon-delimited, latin-1)
        lines = r.content.decode("latin-1").splitlines()
        reader = csv.DictReader(lines, delimiter=";")
        companies = list(reader)

        # Filter to active companies
        active = [c for c in companies if c.get("SIT") == "ATIVO"]

        if search:
            search_lower = search.lower()
            active = [
                c for c in active
                if search_lower in c.get("DENOM_SOCIAL", "").lower()
                or search_lower in c.get("DENOM_COMERC", "").lower()
            ]

        # Return relevant columns
        return [
            {
                "cnpj": c.get("CNPJ_CIA", ""),
                "name": c.get("DENOM_SOCIAL", ""),
                "trade_name": c.get("DENOM_COMERC", ""),
                "cd_cvm": c.get("CD_CVM", ""),
                "sector": c.get("SETOR_ATIV", ""),
            }
            for c in active
        ]

    def download_financials(self, year, report_type="dfp"):
        """
        Download CVM financial data for a given year.
        report_type: 'dfp' (annual) or 'itr' (quarterly)
        Returns dict of {statement_type: list_of_dicts}
        """
        url = (
            f"{CVM_BASE}/DOC/{report_type.upper()}"
            f"/DADOS/{report_type}_cia_aberta_{year}.zip"
        )
        r = self.session.get(url, timeout=120)
        r.raise_for_status()

        dataframes = {}
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for filename in z.namelist():
                if not filename.endswith(".csv"):
                    continue
                with z.open(filename) as f:
                    content = f.read().decode("latin-1")
                    reader = csv.DictReader(content.splitlines(), delimiter=";")
                    rows = list(reader)
                    # Extract statement type from filename
                    # e.g., "dfp_cia_aberta_DRE_con_2023.csv" -> "DRE_con"
                    parts = filename.replace(".csv", "").split("_")
                    # Find the statement code (BPA, BPP, DRE, DFC, etc.)
                    key = filename.replace(".csv", "")
                    dataframes[key] = rows
        return dataframes

    def filter_company(self, data, company_name=None, cnpj=None, cd_cvm=None):
        """Filter CVM data for a specific company."""
        results = {}
        for key, rows in data.items():
            filtered = []
            for row in rows:
                if cnpj and row.get("CNPJ_CIA") == cnpj:
                    filtered.append(row)
                elif cd_cvm and row.get("CD_CVM") == str(cd_cvm):
                    filtered.append(row)
                elif company_name and company_name.lower() in row.get("DENOM_CIA", "").lower():
                    filtered.append(row)
            if filtered:
                results[key] = filtered
        return results

    def extract_income_statement(self, company_data):
        """
        Extract key income statement items from CVM data.
        Looks for DRE (Demonstracao de Resultado) files.
        """
        dre_data = []
        for key, rows in company_data.items():
            if "DRE" not in key.upper():
                continue
            for row in rows:
                # Only take the latest version and current period
                ordem = row.get("ORDEM_EXERC", "")
                if "LTIMO" not in ordem or "PEN" in ordem:
                    continue
                cd_conta = row.get("CD_CONTA", "")
                eng_label = CVM_ACCOUNT_LABELS.get(cd_conta, "")
                dre_data.append({
                    "account_code": cd_conta,
                    "account_desc_pt": row.get("DS_CONTA", ""),
                    "account_desc_en": eng_label,
                    "value_brl": row.get("VL_CONTA", ""),
                    "period_end": row.get("DT_REFER", ""),
                    "period_start": row.get("DT_INI_EXERC", ""),
                    "version": row.get("VERSAO", ""),
                    "company": row.get("DENOM_CIA", ""),
                })
        return dre_data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_edgar_search(args):
    client = EdgarClient()
    results = client.search_companies(args.query)
    if not results:
        print(f"No companies found matching '{args.query}'")
        return
    print(f"\nFound {len(results)} companies matching '{args.query}':\n")
    for r in results[:20]:
        print(f"  CIK: {r['cik']:>10}  Ticker: {r['ticker']:<8}  {r['name']}")


def cmd_edgar_filings(args):
    client = EdgarClient()
    filings, name, tickers = client.get_filings(args.cik, form_type=args.form, limit=args.limit)
    print(f"\n{name} ({', '.join(tickers)})")
    print(f"Recent {args.form} filings:\n")
    for f in filings:
        print(f"  {f['filing_date']}  {f['form']}  {f['description']}")
        print(f"    URL: {f['url']}\n")


def cmd_edgar_financials(args):
    client = EdgarClient()
    results = client.extract_key_financials(args.cik, taxonomy=args.taxonomy)
    if "error" in results:
        print(f"Error: {results['error']}")
        if "available_taxonomies" in results:
            print(f"Available taxonomies: {results['available_taxonomies']}")
        return

    print(f"\n{results['company']} — Key Financials (taxonomy: {results['taxonomy']})\n")
    for tag, info in results["metrics"].items():
        label = info['label'] or tag
        print(f"  {label} ({info['unit']}):")
        for v in info["recent_values"][:4]:
            period = f"{v['start']} to {v['end']}" if v["start"] else v["end"]
            print(f"    {period}: {v['value']:>20,}  (filed {v['filed']}, form {v['form']})")
        print()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Saved to {args.output}")


def cmd_edgar_concept(args):
    client = EdgarClient()
    data = client.get_company_concept(args.cik, args.taxonomy, args.tag)
    print(f"\n{data.get('entityName', '')} — {args.taxonomy}:{args.tag}\n")

    units = data.get("units", {})
    for unit_name, facts in units.items():
        print(f"  Unit: {unit_name}")
        sorted_facts = sorted(
            [f for f in facts if "end" in f],
            key=lambda x: x.get("end", ""),
            reverse=True,
        )
        for f in sorted_facts[:10]:
            period = f"{f.get('start', '')} to {f['end']}" if f.get("start") else f["end"]
            print(f"    {period}: {f['val']:>20,}  (form {f.get('form', '?')}, filed {f.get('filed', '?')})")
        print()


def cmd_cvm_companies(args):
    client = CvmClient()
    companies = client.get_companies(search=args.search)
    if not companies:
        print(f"No active companies found matching '{args.search}'")
        return
    print(f"\nFound {len(companies)} active companies:\n")
    for c in companies[:30]:
        print(f"  CD_CVM: {c['cd_cvm']:>6}  {c['name']}")
        if c["trade_name"]:
            print(f"          Trade name: {c['trade_name']}")
        print(f"          Sector: {c['sector']}")
        print()


def cmd_cvm_dfp(args):
    client = CvmClient()
    print(f"Downloading DFP data for {args.year}...")
    data = client.download_financials(args.year, report_type="dfp")
    print(f"Downloaded {len(data)} files.")

    if args.company:
        filtered = client.filter_company(data, company_name=args.company)
        if not filtered:
            print(f"No data found for '{args.company}'")
            return
        print(f"\nFiltered to {sum(len(v) for v in filtered.values())} rows for '{args.company}'")
        dre = client.extract_income_statement(filtered)
        if dre:
            print(f"\nIncome Statement ({dre[0]['company']}):\n")
            for item in dre:
                label = item["account_desc_en"] or item["account_desc_pt"]
                val = item["value_brl"]
                print(f"  {item['account_code']:>12}  {label:<45}  {val:>15}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(filtered, f, indent=2, default=str, ensure_ascii=False)
            print(f"\nFull data saved to {args.output}")
    else:
        print("\nAvailable files:")
        for key in sorted(data.keys()):
            print(f"  {key}: {len(data[key])} rows")


def cmd_cvm_itr(args):
    client = CvmClient()
    print(f"Downloading ITR data for {args.year}...")
    data = client.download_financials(args.year, report_type="itr")
    print(f"Downloaded {len(data)} files.")

    if args.company:
        filtered = client.filter_company(data, company_name=args.company)
        if not filtered:
            print(f"No data found for '{args.company}'")
            return
        print(f"\nFiltered to {sum(len(v) for v in filtered.values())} rows for '{args.company}'")
        dre = client.extract_income_statement(filtered)
        if dre:
            print(f"\nIncome Statement ({dre[0]['company']}):\n")
            for item in dre:
                label = item["account_desc_en"] or item["account_desc_pt"]
                val = item["value_brl"]
                print(f"  {item['account_code']:>12}  {label:<45}  {val:>15}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(filtered, f, indent=2, default=str, ensure_ascii=False)
            print(f"\nFull data saved to {args.output}")
    else:
        print("\nAvailable files:")
        for key in sorted(data.keys()):
            print(f"  {key}: {len(data[key])} rows")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch earnings reports for Latin American companies"
    )
    subparsers = parser.add_subparsers(dest="source", required=True)

    # --- EDGAR commands ---
    edgar = subparsers.add_parser("edgar", help="SEC EDGAR (US-listed LatAm companies)")
    edgar_sub = edgar.add_subparsers(dest="command", required=True)

    # edgar search
    p = edgar_sub.add_parser("search", help="Search for a company")
    p.add_argument("query", help="Company name or ticker")
    p.set_defaults(func=cmd_edgar_search)

    # edgar filings
    p = edgar_sub.add_parser("filings", help="Get filing history")
    p.add_argument("cik", type=int, help="CIK number")
    p.add_argument("--form", default="20-F", help="Form type (default: 20-F)")
    p.add_argument("--limit", type=int, default=10, help="Max filings to return")
    p.set_defaults(func=cmd_edgar_filings)

    # edgar financials
    p = edgar_sub.add_parser("financials", help="Get XBRL financial data")
    p.add_argument("cik", type=int, help="CIK number")
    p.add_argument("--taxonomy", default="ifrs-full", help="XBRL taxonomy (default: ifrs-full)")
    p.add_argument("--output", "-o", help="Output JSON file path")
    p.set_defaults(func=cmd_edgar_financials)

    # edgar concept
    p = edgar_sub.add_parser("concept", help="Get a specific financial metric")
    p.add_argument("cik", type=int, help="CIK number")
    p.add_argument("taxonomy", help="Taxonomy (e.g., ifrs-full, us-gaap)")
    p.add_argument("tag", help="XBRL tag (e.g., Revenue, ProfitLoss)")
    p.set_defaults(func=cmd_edgar_concept)

    # --- CVM commands ---
    cvm = subparsers.add_parser("cvm", help="CVM Brazil (B3-listed companies)")
    cvm_sub = cvm.add_subparsers(dest="command", required=True)

    # cvm companies
    p = cvm_sub.add_parser("companies", help="List/search CVM companies")
    p.add_argument("--search", help="Search by company name")
    p.set_defaults(func=cmd_cvm_companies)

    # cvm dfp
    p = cvm_sub.add_parser("dfp", help="Download annual financial data (DFP)")
    p.add_argument("year", type=int, help="Year to download")
    p.add_argument("--company", help="Filter by company name")
    p.add_argument("--output", "-o", help="Output JSON file path")
    p.set_defaults(func=cmd_cvm_dfp)

    # cvm itr
    p = cvm_sub.add_parser("itr", help="Download quarterly financial data (ITR)")
    p.add_argument("year", type=int, help="Year to download")
    p.add_argument("--company", help="Filter by company name")
    p.add_argument("--output", "-o", help="Output JSON file path")
    p.set_defaults(func=cmd_cvm_itr)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

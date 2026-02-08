#!/usr/bin/env python3
"""
Census Bureau API helper — reusable functions for fetching and discovering data.

This script can be used standalone or imported as a module.

Standalone usage:
    # Search for variables
    python scripts/census_fetch.py search 2023 acs5 "median household income"

    # Fetch data
    python scripts/census_fetch.py fetch 2023 acs5 "NAME,B19013_001E" "state:*"

    # Fetch with geography nesting
    python scripts/census_fetch.py fetch 2023 acs5 "NAME,B19013_001E" "county:*" --in "state:06"

    # Discover POPGROUP codes
    python scripts/census_fetch.py popgroups 2023 "mexican"

    # List available datasets
    python scripts/census_fetch.py datasets

Module usage:
    from scripts.census_fetch import CensusFetcher
    fetcher = CensusFetcher()
    data = fetcher.fetch(2023, "acs5", ["NAME", "B19013_001E"], geo_for="state:*")
"""

import requests
import json
import csv
import sys
import argparse


# ---------------------------------------------------------------------------
# Endpoint registry
# ---------------------------------------------------------------------------

ENDPOINTS = {
    "acs5":         "/acs/acs5",
    "acs1":         "/acs/acs1",
    "acs5_subject": "/acs/acs5/subject",
    "acs1_subject": "/acs/acs1/subject",
    "acs5_profile": "/acs/acs5/profile",
    "acs1_profile": "/acs/acs1/profile",
    "acs5_cprofile":"/acs/acs5/cprofile",
    "acs1_spp":     "/acs/acs1/spp",
    "dec_pl":       "/dec/pl",
    "cbp":          "/cbp",
    "pep":          "/pep/population",
}

BASE = "https://api.census.gov/data"

NULL_VALUES = {None, "", "-", "N", "(X)", "null", "**", "***", "-666666666", "-666666666.0"}


class CensusFetcher:
    """Stateless helper for Census Bureau API calls."""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Core fetch
    # ------------------------------------------------------------------

    def fetch(self, year, endpoint_key, variables, geo_for,
              geo_in=None, extra_params=None):
        """
        Fetch data from the Census API.

        Args:
            year: Data year (e.g. 2023)
            endpoint_key: Key from ENDPOINTS dict (e.g. "acs5", "acs1_spp")
            variables: List of variable names, or comma-separated string
            geo_for: Geography spec (e.g. "state:*", "county:*")
            geo_in: Optional parent geography (e.g. "state:06")
            extra_params: Optional dict of additional params (e.g. {"POPGROUP": "400"})

        Returns:
            List of dicts (one per row), or None on failure.
        """
        if isinstance(variables, list):
            variables = ",".join(variables)

        path = ENDPOINTS.get(endpoint_key)
        if not path:
            print(f"Unknown endpoint key: {endpoint_key}")
            print(f"Available: {', '.join(sorted(ENDPOINTS.keys()))}")
            return None

        url = f"{BASE}/{year}{path}"
        params = {"get": variables, "for": geo_for}
        if geo_in:
            params["in"] = geo_in
        if extra_params:
            params.update(extra_params)
        if self.api_key:
            params["key"] = self.api_key

        try:
            r = self.session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

        if r.status_code == 204:
            print(f"204 No Content — data not available for this combination.")
            print(f"  Try a different year, geography, or group code.")
            return None
        if r.status_code != 200:
            print(f"HTTP {r.status_code}: {r.text[:300]}")
            return None

        try:
            raw = r.json()
        except json.JSONDecodeError:
            print(f"Invalid JSON response: {r.text[:200]}")
            return None

        if len(raw) < 2:
            print("Response had no data rows.")
            return None

        header = raw[0]
        rows = raw[1:]
        return [dict(zip(header, row)) for row in rows]

    # ------------------------------------------------------------------
    # Variable discovery
    # ------------------------------------------------------------------

    def search_variables(self, year, endpoint_key, keyword):
        """
        Search for variable names matching a keyword.

        Returns list of (variable_name, label) tuples.
        """
        path = ENDPOINTS.get(endpoint_key)
        if not path:
            print(f"Unknown endpoint key: {endpoint_key}")
            print(f"Available: {', '.join(sorted(ENDPOINTS.keys()))}")
            return []
        url = f"{BASE}/{year}{path}/variables.json"

        try:
            r = self.session.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return []

        if r.status_code != 200:
            print(f"HTTP {r.status_code} fetching variables list")
            return []

        variables = r.json().get("variables", {})
        keyword_lower = keyword.lower()
        matches = []
        for name, info in variables.items():
            label = info.get("label", "")
            if keyword_lower in label.lower():
                matches.append((name, label))

        return sorted(matches, key=lambda x: x[0])

    # ------------------------------------------------------------------
    # POPGROUP discovery (for SPP endpoint)
    # ------------------------------------------------------------------

    def search_popgroups(self, year, keyword=None):
        """
        Search POPGROUP codes for the Selected Population Profiles endpoint.

        Returns list of (code, label) tuples.
        """
        url = f"{BASE}/{year}/acs/acs1/spp/variables/POPGROUP.json"

        try:
            r = self.session.get(url, timeout=15)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return []

        if r.status_code != 200:
            print(f"HTTP {r.status_code} fetching POPGROUP codes")
            return []

        items = r.json().get("values", {}).get("item", {})

        if keyword:
            keyword_lower = keyword.lower()
            items = {k: v for k, v in items.items()
                     if keyword_lower in v.lower()}

        return sorted(items.items(),
                       key=lambda x: int(x[0]) if x[0].isdigit() else 0)

    # ------------------------------------------------------------------
    # Dataset listing
    # ------------------------------------------------------------------

    def list_datasets(self):
        """List major available dataset categories."""
        url = f"{BASE}.json"
        try:
            r = self.session.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return []

        if r.status_code != 200:
            return []

        datasets = r.json().get("dataset", [])
        return [(d.get("title", ""), d.get("c_vintage", ""),
                 d.get("identifier", "")) for d in datasets[:50]]


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def clean_value(val):
    """Convert a Census API value to float, returning None for nulls."""
    if val in NULL_VALUES:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def save_csv(records, filepath, fields=None):
    """Save list of dicts to CSV."""
    if not records:
        print("No records to save.")
        return
    if fields is None:
        fields = list(records[0].keys())
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} rows to {filepath}")


def save_json(records, filepath):
    """Save list of dicts to JSON."""
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved {len(records)} records to {filepath}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Census Bureau API helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search 2023 acs5 "median household income"
  %(prog)s fetch 2023 acs5 "NAME,B19013_001E" "state:*"
  %(prog)s fetch 2023 acs5 "NAME,B19013_001E" "county:*" --in "state:06"
  %(prog)s fetch 2023 acs1_spp "NAME,S0201_214E" "us:1" --param POPGROUP=400
  %(prog)s popgroups 2023 "mexican"
  %(prog)s datasets
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # --- search ---
    p_search = sub.add_parser("search", help="Search for variable names")
    p_search.add_argument("year", type=int)
    p_search.add_argument("endpoint", choices=sorted(ENDPOINTS.keys()))
    p_search.add_argument("keyword")

    # --- fetch ---
    p_fetch = sub.add_parser("fetch", help="Fetch data from Census API")
    p_fetch.add_argument("year", type=int)
    p_fetch.add_argument("endpoint", choices=sorted(ENDPOINTS.keys()))
    p_fetch.add_argument("variables", help="Comma-separated variable names")
    p_fetch.add_argument("geo_for", help='Geography (e.g. "state:*")')
    p_fetch.add_argument("--in", dest="geo_in", help='Parent geography (e.g. "state:06")')
    p_fetch.add_argument("--param", action="append", help="Extra param as KEY=VALUE")
    p_fetch.add_argument("-o", "--output", help="Output CSV file path")

    # --- popgroups ---
    p_pop = sub.add_parser("popgroups", help="Search POPGROUP codes")
    p_pop.add_argument("year", type=int)
    p_pop.add_argument("keyword", nargs="?", default=None)

    # --- datasets ---
    sub.add_parser("datasets", help="List available datasets")

    args = parser.parse_args()
    fetcher = CensusFetcher()

    if args.command == "search":
        results = fetcher.search_variables(args.year, args.endpoint, args.keyword)
        if results:
            print(f"\n{len(results)} variables matching '{args.keyword}':\n")
            for name, label in results[:40]:
                print(f"  {name:20s}  {label}")
            if len(results) > 40:
                print(f"\n  ... and {len(results) - 40} more")
        else:
            print(f"No variables found matching '{args.keyword}'")

    elif args.command == "fetch":
        extra = {}
        if args.param:
            for p in args.param:
                if "=" not in p:
                    print(f"Error: Invalid parameter format '{p}'. Use KEY=VALUE.", file=sys.stderr)
                    sys.exit(1)
                k, v = p.split("=", 1)
                extra[k] = v

        data = fetcher.fetch(
            args.year, args.endpoint, args.variables,
            args.geo_for, args.geo_in, extra or None,
        )
        if data:
            print(f"\nFetched {len(data)} rows.\n")
            # Print first 5 rows
            for row in data[:5]:
                print(f"  {row}")
            if len(data) > 5:
                print(f"  ... ({len(data) - 5} more rows)")

            if args.output:
                save_csv(data, args.output)

    elif args.command == "popgroups":
        results = fetcher.search_popgroups(args.year, args.keyword)
        if results:
            kw = f" matching '{args.keyword}'" if args.keyword else ""
            print(f"\n{len(results)} POPGROUP codes{kw}:\n")
            for code, label in results[:50]:
                print(f"  {code:6s}  {label}")
            if len(results) > 50:
                print(f"\n  ... and {len(results) - 50} more")
        else:
            print("No POPGROUP codes found")

    elif args.command == "datasets":
        datasets = fetcher.list_datasets()
        if datasets:
            print(f"\nFirst {len(datasets)} datasets:\n")
            for title, vintage, ident in datasets:
                v = f" ({vintage})" if vintage else ""
                print(f"  {title}{v}")
        else:
            print("Could not fetch dataset list")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

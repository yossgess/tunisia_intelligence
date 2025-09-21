"""
Unified CLI/dispatcher for RSS extractors

Usage examples:
- python main.py --url https://nawaat.org/feed/
- python main.py --url https://www.radiotunisienne.tn/articles/rss --output json
- python main.py --list  # show all registered feeds

This script routes a given RSS URL to its dedicated extractor from the
`extractors/` package. It tries an exact URL match first, then falls back
to a domain-level match.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable, Dict, List
from urllib.parse import urlparse

from extractors import EXTRACTOR_REGISTRY, DOMAIN_REGISTRY


def resolve_extractor(url: str) -> Callable[[str], List[Dict[str, Any]]]:
    # Exact URL match
    if url in EXTRACTOR_REGISTRY:
        return EXTRACTOR_REGISTRY[url]

    # Domain fallback
    try:
        domain = urlparse(url).netloc
        # Normalize: drop leading www.
        domain = domain[4:] if domain.startswith("www.") else domain
        if domain in DOMAIN_REGISTRY:
            return DOMAIN_REGISTRY[domain]
    except Exception:
        pass

    raise SystemExit(
        f"No extractor found for URL: {url}\n"
        f"- Try one of the registered URLs using --list\n"
    )


essential_fields = ["title", "link", "description", "pub_date", "content"]


def print_human(entries: List[Dict[str, Any]]) -> None:
    for i, item in enumerate(entries, 1):
        print(f"Item {i}:")
        for key in essential_fields:
            print(f"  {key.capitalize()}: {item.get(key, '')}")
        print("-" * 80)


def print_json(entries: List[Dict[str, Any]]) -> None:
    print(json.dumps(entries, ensure_ascii=False, indent=2))


def list_registered() -> None:
    print("Registered feed URLs (exact matches):")
    for url in sorted(EXTRACTOR_REGISTRY.keys()):
        print(f"- {url}")

    print("\nRegistered domains (fallbacks):")
    for domain in sorted(DOMAIN_REGISTRY.keys()):
        print(f"- {domain}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="RSS Extractors Dispatcher")
    parser.add_argument("--url", help="RSS feed URL to parse")
    parser.add_argument(
        "--output",
        choices=["human", "json"],
        default="human",
        help="Output format",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered feeds and exit",
    )

    args = parser.parse_args(argv)

    if args.list:
        list_registered()
        return

    if not args.url:
        parser.error("--url is required unless --list is provided")

    extractor = resolve_extractor(args.url)
    entries = extractor(args.url)

    if args.output == "json":
        print_json(entries)
    else:
        print_human(entries)


if __name__ == "__main__":
    main(sys.argv[1:])

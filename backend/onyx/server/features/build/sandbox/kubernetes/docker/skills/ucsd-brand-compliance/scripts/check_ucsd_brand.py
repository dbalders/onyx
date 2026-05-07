#!/usr/bin/env python3
"""Scan web source files for UC San Diego brand colors and calculate contrast."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BRAND_COLORS = {
    "#182B49": "ucsd-navy",
    "#00629B": "ucsd-blue",
    "#FFCD00": "ucsd-yellow",
    "#C69214": "ucsd-gold",
    "#00C6D7": "ucsd-teal",
    "#D462AD": "ucsd-magenta",
    "#F5F0E6": "ucsd-sand",
    "#F3E500": "ucsd-citron",
    "#FC8900": "ucsd-orange",
    "#6E963B": "ucsd-green",
    "#747678": "ucsd-cool-gray",
    "#B6B1A9": "ucsd-warm-gray",
    "#FFFFFF": "ucsd-white",
    "#000000": "ucsd-black",
}

SCAN_EXTENSIONS = {
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".htm",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".astro",
}

SKIP_DIRS = {
    ".git",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
}

HEX_RE = re.compile(
    r"(?<![A-Za-z0-9_-])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})(?![A-Za-z0-9_-])"
)


def normalize_hex(value: str) -> str | None:
    raw = value.strip().upper()
    if len(raw) == 4:
        return "#" + "".join(char * 2 for char in raw[1:])
    if len(raw) == 5:
        return "#" + "".join(char * 2 for char in raw[1:4])
    if len(raw) == 7:
        return raw
    if len(raw) == 9:
        return raw[:7]
    return None


def srgb_to_linear(channel: int) -> float:
    value = channel / 255
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    normalized = normalize_hex(hex_color)
    if normalized is None:
        raise ValueError(f"Invalid hex color: {hex_color}")
    red = int(normalized[1:3], 16)
    green = int(normalized[3:5], 16)
    blue = int(normalized[5:7], 16)
    return (
        0.2126 * srgb_to_linear(red)
        + 0.7152 * srgb_to_linear(green)
        + 0.0722 * srgb_to_linear(blue)
    )


def contrast_ratio(foreground: str, background: str) -> float:
    first = luminance(foreground)
    second = luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def iter_files(paths: list[Path]):
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in SCAN_EXTENSIONS:
                yield path
            continue
        for candidate in path.rglob("*"):
            if any(part in SKIP_DIRS for part in candidate.parts):
                continue
            if candidate.is_file() and candidate.suffix.lower() in SCAN_EXTENSIONS:
                yield candidate


def scan(paths: list[Path]):
    counts: Counter[str] = Counter()
    locations: dict[str, list[str]] = defaultdict(list)
    files_scanned = 0

    for file_path in iter_files(paths):
        files_scanned += 1
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="latin-1")

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in HEX_RE.finditer(line):
                normalized = normalize_hex(match.group(0))
                if normalized is None:
                    continue
                counts[normalized] += 1
                if len(locations[normalized]) < 8:
                    locations[normalized].append(f"{file_path}:{line_number}")

    approved = {
        color: {"name": BRAND_COLORS[color], "count": count, "locations": locations[color]}
        for color, count in sorted(counts.items())
        if color in BRAND_COLORS
    }
    non_brand = {
        color: {"count": count, "locations": locations[color]}
        for color, count in sorted(counts.items())
        if color not in BRAND_COLORS
    }
    return {
        "files_scanned": files_scanned,
        "approved": approved,
        "non_brand": non_brand,
    }


def print_report(result: dict):
    print(f"Files scanned: {result['files_scanned']}")
    print()
    print("Approved UCSD colors:")
    if not result["approved"]:
        print("  None found")
    for color, data in result["approved"].items():
        print(f"  {color} ({data['name']}): {data['count']}")
        for location in data["locations"]:
            print(f"    {location}")

    print()
    print("Non-brand hex colors:")
    if not result["non_brand"]:
        print("  None found")
    for color, data in result["non_brand"].items():
        print(f"  {color}: {data['count']}")
        for location in data["locations"]:
            print(f"    {location}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Print scan results as JSON")
    parser.add_argument(
        "--contrast",
        nargs=2,
        metavar=("FOREGROUND", "BACKGROUND"),
        help="Calculate contrast ratio for two hex colors",
    )
    args = parser.parse_args()

    if args.contrast:
        ratio = contrast_ratio(args.contrast[0], args.contrast[1])
        passes_aa_normal = ratio >= 4.5
        passes_aa_large = ratio >= 3
        print(f"Contrast ratio: {ratio:.2f}:1")
        print(f"WCAG AA normal text: {'pass' if passes_aa_normal else 'fail'}")
        print(f"WCAG AA large text/UI: {'pass' if passes_aa_large else 'fail'}")
        return 0

    if not args.paths:
        parser.error("provide at least one path to scan, or use --contrast")

    result = scan(args.paths)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

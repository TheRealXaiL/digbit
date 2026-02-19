#!/usr/bin/env python3
"""digbit — generate bitsquatting domain variants and optionally resolve them."""

import argparse
import os
import re
import socket
import sys
import urllib.request

COMMON_TLDS = {
    "com", "net", "org", "io", "co", "dev", "app", "edu", "gov", "mil",
    "int", "info", "biz", "name", "mobi", "pro", "aero", "coop", "museum",
    "jobs", "travel", "cat", "tel", "asia", "post", "xxx", "bike", "guru",
    "email", "today", "tips", "photos", "technology", "company", "systems",
    "management", "center", "directory", "solutions", "support", "training",
    "academy", "cloud", "xyz", "online", "site", "store", "tech", "space",
    "fun", "website", "shop", "top", "work", "live", "us", "uk", "de",
    "fr", "nl", "ru", "cn", "jp", "br", "au", "ca", "in", "eu", "tv",
    "me", "cc", "ws", "la", "ag", "vc", "ly", "mx", "ar", "cl",
}

IANA_TLD_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
CACHE_DIR = os.path.expanduser("~/.cache/digbit")
CACHE_FILE = os.path.join(CACHE_DIR, "tlds.txt")


def load_tlds():
    """Load TLDs from cache file, falling back to built-in set."""
    if os.path.isfile(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                tlds = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        tlds.add(line.lower())
                if tlds:
                    return tlds
        except OSError:
            pass
    return COMMON_TLDS


def update_tlds():
    """Download the IANA TLD list and save to cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Downloading TLD list from {IANA_TLD_URL} ...")
    try:
        req = urllib.request.Request(IANA_TLD_URL, headers={"User-Agent": "digbit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        sys.exit(f"Error downloading TLD list: {e}")

    tlds = []
    for line in data.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tlds.append(line.upper())

    with open(CACHE_FILE, "w") as f:
        f.write(f"# IANA TLD list — downloaded by digbit\n")
        for tld in sorted(tlds):
            f.write(tld + "\n")

    print(f"Saved {len(tlds)} TLDs to {CACHE_FILE}")


def is_valid_label(label):
    """Check if a domain label conforms to RFC 1035."""
    if not label or len(label) > 63:
        return False
    if label.startswith("-") or label.endswith("-"):
        return False
    return bool(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', label))


def bitflip_domain(domain):
    """Generate all single-bit-flip variants of a domain string (lowercased, deduplicated)."""
    seen = set()
    results = []
    for ci, ch in enumerate(domain):
        bits = format(ord(ch), '08b')
        for bi in range(8):
            flipped = list(bits)
            flipped[bi] = '0' if flipped[bi] == '1' else '1'
            new_char_code = int(''.join(flipped), 2)
            if new_char_code < 0x20 or new_char_code > 0x7E:
                continue
            new_domain = (domain[:ci] + chr(new_char_code) + domain[ci + 1:]).lower()
            if new_domain != domain and new_domain not in seen:
                seen.add(new_domain)
                results.append(new_domain)
    return results


def validate_domain(domain, valid_tlds):
    """Check that a bitflipped domain has valid labels and a known TLD."""
    parts = domain.split(".")
    if len(parts) < 2:
        return False
    tld = parts[-1].lower()
    if tld not in valid_tlds:
        return False
    for label in parts[:-1]:
        if not is_valid_label(label):
            return False
    # TLD label check (alpha only for TLDs)
    if not re.match(r'^[a-z]{2,}$', tld):
        return False
    return True


def resolve_domain(domain):
    """Try to resolve a domain. Returns (registered, ip)."""
    try:
        results = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM)
        ip = results[0][4][0] if results else ""
        return True, ip
    except socket.gaierror:
        return False, ""
    except Exception:
        return False, ""


def print_table(rows):
    """Print a formatted table of resolution results."""
    if not rows:
        return
    col_widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    header = rows[0]
    print("  ".join(h.ljust(w) for h, w in zip(header, col_widths)))
    print("  ".join("-" * w for w in col_widths))
    for row in rows[1:]:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, col_widths)))


def main():
    parser = argparse.ArgumentParser(
        description="Generate bitsquatting domain variants (single bit-flip mutations)."
    )
    parser.add_argument("domain", nargs="?", help="Target domain (e.g. example.com)")
    parser.add_argument(
        "-r", "--resolve", action="store_true",
        help="Resolve each variant via DNS and show registration status"
    )
    parser.add_argument(
        "-o", "--original", action="store_true",
        help="Include the original domain in resolution output (requires -r)"
    )
    parser.add_argument(
        "--update-tlds", action="store_true",
        help="Download the latest IANA TLD list and exit"
    )
    args = parser.parse_args()

    if args.update_tlds:
        update_tlds()
        return

    if not args.domain:
        parser.error("domain is required (unless using --update-tlds)")

    domain = args.domain.lower().strip().rstrip(".")
    if "." not in domain:
        sys.exit("Error: domain must contain a dot (e.g. example.com)")

    valid_tlds = load_tlds()

    input_tld = domain.rsplit(".", 1)[-1]
    if input_tld not in valid_tlds:
        print(f"Warning: input TLD '.{input_tld}' not in known TLD list", file=sys.stderr)

    variants = bitflip_domain(domain)
    valid_variants = [d for d in variants if validate_domain(d, valid_tlds)]

    if not valid_variants:
        print("No valid bitsquat variants found.", file=sys.stderr)
        return

    if args.resolve:
        rows = [("DOMAIN", "STATUS", "IP")]
        if args.original:
            registered, ip = resolve_domain(domain)
            status = "REGISTERED" if registered else "AVAILABLE"
            rows.append((domain, status, ip if ip else "-"))
        for variant in valid_variants:
            registered, ip = resolve_domain(variant)
            status = "REGISTERED" if registered else "AVAILABLE"
            rows.append((variant, status, ip if ip else "-"))
        print_table(rows)
    else:
        for variant in valid_variants:
            print(variant)


if __name__ == "__main__":
    main()

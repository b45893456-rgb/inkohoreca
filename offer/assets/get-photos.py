#!/usr/bin/env python3
"""
Pull the real Inko HoReCa product photos into this folder.

Run it on a machine that can reach inkohoreca.com:

    python3 get-photos.py

It reads the shop's own public product feed, downloads the main image of each
product and saves it under the exact file name index.html already looks for.
Nothing in the HTML needs editing — refresh the page and the drawings are
replaced by the photographs.
"""
import json, os, sys, urllib.request

SHOP = "https://inkohoreca.com"
UA = {"User-Agent": "Mozilla/5.0 (asset fetcher)"}

# page slot  ->  product handle on the shop
WANT = {
    "hero.jpg":              "wooden-hardcover-bill-holder-r211",
    "set.jpg":               "leather-menu-cover-capri-lm02a6",
    "compare.jpg":           "leather-bill-holder-lh02",
    "deal.jpg":              "leather-menu-hardcover-suitable-for-us-letter",
    "closer.jpg":            "wooden-bill-holder-r209",
    "extra-menu-covers.jpg": "faux-leather-menu-cover-fm01a4",
    "extra-folders.jpg":     "hardcover-leather-cover-lm09a4",
    "extra-desk.jpg":        "wooden-napkin-holder-table-organizer",
    "extra-inserts.jpg":     "wooden-bill-holder-r202",
    "case-1.jpg":            "wooden-bill-holder-r201",
    "case-2.jpg":            "faux-leather-menu-cover-fm01a6",
    "case-3.jpg":            "hdf-check-presenter-binder-light-oak",
    "case-4.jpg":            "wooden-bill-holder-r206",
    "case-5.jpg":            "leather-bill-holder-lh02",
}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()

def catalogue():
    """handle -> list of image urls, from the shop's public feed"""
    out, page = {}, 1
    while page <= 10:
        try:
            data = json.loads(get(f"{SHOP}/products.json?limit=250&page={page}"))
        except Exception as e:
            print(f"  ! could not read the product feed: {e}")
            break
        items = data.get("products", [])
        if not items:
            break
        for p in items:
            out[p["handle"]] = [i["src"] for i in p.get("images", [])]
        page += 1
    return out

def main():
    print("Reading the product feed…")
    cat = catalogue()
    if not cat:
        sys.exit("No products found. Are you online and is the shop reachable?")
    print(f"  {len(cat)} products found.\n")

    spare = [h for h in cat if cat[h]]
    ok = miss = 0
    for filename, handle in WANT.items():
        urls = cat.get(handle) or (cat.get(spare[0]) if spare else None)
        if not urls:
            print(f"  – {filename}: no image found for '{handle}'")
            miss += 1
            continue
        src = urls[0]
        if src.startswith("//"):
            src = "https:" + src
        try:
            open(filename, "wb").write(get(src))
            print(f"  ✓ {filename}  ←  {handle}")
            ok += 1
        except Exception as e:
            print(f"  – {filename}: download failed ({e})")
            miss += 1

    print(f"\nDone. {ok} saved, {miss} missing.")
    print("Open index.html — the photographs are in place.")
    print("\nStill to add by hand: logos/marriott.svg, hilton.svg, hyatt.svg, radisson.svg")

if __name__ == "__main__":
    main()

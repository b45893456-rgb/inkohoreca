#!/usr/bin/env python3
"""
Pull the real Inko HoReCa imagery into this folder.

Run it on a machine that can reach inkohoreca.com:

    python3 get-photos.py

What it does, in order:
  1. reads the shop's public product feed and saves each product's main photo
     under the exact file name index.html already looks for;
  2. scans the shop home page for the hotel-brand logos and saves them to
     logos/ (marriott.svg, hilton.svg, hyatt.svg, radisson.svg);
  3. saves the remaining large home-page images to candidates/ so you can pick
     a lifestyle shot for the hero.

Nothing in the HTML needs editing — refresh the page and the drawings are
replaced by the photographs.
"""
import json, os, re, sys, urllib.parse, urllib.request

SHOP = "https://inkohoreca.com"
UA = {"User-Agent": "Mozilla/5.0 (asset fetcher)"}

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

BRANDS = ["marriott", "hilton", "hyatt", "radisson"]


def get(url, timeout=30):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=timeout).read()


def abs_url(u):
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return SHOP + u
    return u


def save(url, path):
    data = get(abs_url(url))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "wb").write(data)
    return len(data)


# ---------------------------------------------------------------- products
def products():
    out, page = {}, 1
    while page <= 10:
        try:
            data = json.loads(get(f"{SHOP}/products.json?limit=250&page={page}"))
        except Exception as e:
            print(f"  ! product feed unavailable: {e}")
            break
        items = data.get("products", [])
        if not items:
            break
        for p in items:
            out[p["handle"]] = [i["src"] for i in p.get("images", [])]
        page += 1
    return out


def step_products():
    print("1. Product photos")
    cat = products()
    if not cat:
        print("   no products read — skipping\n")
        return
    print(f"   {len(cat)} products in the feed")
    spare = [h for h in cat if cat[h]]
    ok = 0
    for filename, handle in WANT.items():
        urls = cat.get(handle) or (cat.get(spare[0]) if spare else None)
        if not urls:
            print(f"   – {filename}: nothing for '{handle}'")
            continue
        try:
            save(urls[0], filename)
            print(f"   ✓ {filename}  ←  {handle}")
            ok += 1
        except Exception as e:
            print(f"   – {filename}: {e}")
    print(f"   {ok}/{len(WANT)} saved\n")


# ------------------------------------------------------------------- logos
def home_images():
    """every image URL referenced by the home page, in document order"""
    try:
        html = get(SHOP).decode("utf-8", "replace")
    except Exception as e:
        print(f"   ! home page unavailable: {e}")
        return []
    urls = re.findall(r'(?:src|data-src|srcset|content)="([^"]+?\.(?:png|jpe?g|svg|webp)[^"]*)"', html)
    urls += re.findall(r"url\((?:'|\")?([^'\")]+?\.(?:png|jpe?g|svg|webp)[^'\")]*)", html)
    seen, out = set(), []
    for u in urls:
        u = u.split()[0].strip()
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def step_logos(imgs):
    print("2. Hotel brand logos")
    if not imgs:
        print("   no home-page images found — skipping\n")
        return
    found = 0
    for brand in BRANDS:
        hit = next((u for u in imgs if brand in u.lower()), None)
        if not hit:
            print(f"   – {brand}: not found on the home page by name")
            continue
        ext = ".svg" if ".svg" in hit.lower() else ".png"
        try:
            save(hit, f"logos/{brand}{ext}")
            print(f"   ✓ logos/{brand}{ext}")
            found += 1
        except Exception as e:
            print(f"   – {brand}: {e}")
    if found < len(BRANDS):
        print("   Logos the shop names differently end up in candidates/ below —")
        print("   rename the right ones to logos/marriott.svg etc.")
    print()


# -------------------------------------------------------------- candidates
def step_candidates(imgs):
    print("3. Other home-page images → candidates/")
    if not imgs:
        print("   nothing to collect\n")
        return
    n = 0
    for u in imgs:
        if any(b in u.lower() for b in BRANDS):
            continue
        name = os.path.basename(urllib.parse.urlparse(abs_url(u)).path) or f"img{n}.jpg"
        try:
            size = save(u, f"candidates/{name}")
            if size < 8000:                      # icons and sprites, not photographs
                os.remove(f"candidates/{name}")
                continue
            n += 1
        except Exception:
            continue
        if n >= 40:
            break
    print(f"   {n} images saved. Pick a lifestyle shot and copy it over hero.jpg.\n")


if __name__ == "__main__":
    print(f"Fetching imagery from {SHOP}\n")
    step_products()
    imgs = home_images()
    step_logos(imgs)
    step_candidates(imgs)
    print("Done. Open index.html.")

#!/usr/bin/env python3
"""
Fill every page's assets/ folder with the real Inko HoReCa imagery.

Run from the project root, on a machine that can reach inkohoreca.com:

    python3 get-photos.py

Three passes:
  1. product photos      — from the shop's public feed (/products.json)
  2. hotel brand logos   — scanned off the shop home page into */assets/logos/
  3. everything else big — into candidates/, to pick a lifestyle hero from

Only Python 3 is needed. No HTML is edited: each page already points at these
file names and falls back to a brand drawing until the file exists.
"""
import json, os, re, sys, urllib.parse, urllib.request

SHOP = "https://inkohoreca.com"
UA = {"User-Agent": "Mozilla/5.0 (asset fetcher)"}
PAGES = ["landing", "advertorial", "offer"]
BRANDS = ["marriott", "hilton", "hyatt", "radisson"]

# product handle -> the file names each page expects
SLOTS = {
    "wooden-hardcover-bill-holder-r211": [
        "landing/assets/hero-set.jpg", "landing/assets/cat-check-presenters.jpg",
        "landing/assets/p-r211.jpg", "advertorial/assets/hero-set.jpg",
        "advertorial/assets/p-r211.jpg", "offer/assets/hero.jpg"],
    "leather-bill-holder-lh02": [
        "advertorial/assets/check-presenter.jpg", "advertorial/assets/p-lh02.jpg",
        "offer/assets/compare.jpg", "offer/assets/case-5.jpg",
        "landing/assets/case-1.jpg"],
    "wooden-bill-holder-r201": [
        "advertorial/assets/p-r201.jpg", "offer/assets/case-1.jpg",
        "landing/assets/case-2.jpg"],
    "wooden-bill-holder-r202": [
        "offer/assets/extra-inserts.jpg", "landing/assets/case-3.jpg"],
    "wooden-bill-holder-r209": [
        "offer/assets/closer.jpg", "advertorial/assets/logo-treatments.jpg",
        "landing/assets/case-4.jpg"],
    "wooden-bill-holder-r206": [
        "offer/assets/case-4.jpg", "landing/assets/case-5.jpg"],
    "hdf-check-presenter-binder-light-oak": [
        "offer/assets/case-3.jpg", "landing/assets/case-6.jpg"],
    "leather-menu-cover-capri-lm02a6": [
        "landing/assets/cat-menu-covers.jpg", "landing/assets/p-lm02a6.jpg",
        "advertorial/assets/p-lm02a6.jpg", "offer/assets/set.jpg",
        "offer/assets/extra-menu-covers.jpg"],
    "faux-leather-menu-cover-fm01a4": [
        "advertorial/assets/p-fm01a4.jpg", "offer/assets/case-2.jpg"],
    "faux-leather-menu-cover-fm01a6": [
        "landing/assets/cat-folders.jpg"],
    "hardcover-leather-cover-lm09a4": [
        "offer/assets/extra-folders.jpg"],
    "leather-menu-hardcover-suitable-for-us-letter": [
        "landing/assets/p-lm12a2.jpg", "advertorial/assets/p-lm12a2.jpg",
        "offer/assets/deal.jpg"],
    "wooden-napkin-holder-table-organizer": [
        "landing/assets/cat-desk.jpg", "offer/assets/extra-desk.jpg"],
}


def get(url, timeout=30):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=timeout).read()


def abs_url(u):
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return SHOP + u
    return u


def save(data, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "wb").write(data)


def products():
    out, page = {}, 1
    while page <= 10:
        try:
            data = json.loads(get(f"{SHOP}/products.json?limit=250&page={page}"))
        except Exception as e:
            print(f"   ! product feed unavailable: {e}")
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
        print("   nothing read — skipping\n")
        return
    print(f"   {len(cat)} products in the feed")
    spare = next((h for h in cat if cat[h]), None)
    written = 0
    for handle, targets in SLOTS.items():
        urls = cat.get(handle) or cat.get(spare)
        if not urls:
            print(f"   – {handle}: no image")
            continue
        try:
            blob = get(abs_url(urls[0]))
        except Exception as e:
            print(f"   – {handle}: {e}")
            continue
        for t in targets:
            save(blob, t)
            written += 1
        tag = "" if cat.get(handle) else "  (stand-in — handle not found)"
        print(f"   ✓ {handle} → {len(targets)} slots{tag}")
    print(f"   {written} files written\n")


def home_images():
    try:
        html = get(SHOP).decode("utf-8", "replace")
    except Exception as e:
        print(f"   ! home page unavailable: {e}")
        return []
    urls = re.findall(
        r'(?:src|data-src|srcset|content)="([^"]+?\.(?:png|jpe?g|svg|webp)[^"]*)"', html)
    urls += re.findall(
        r"url\((?:'|\")?([^'\")]+?\.(?:png|jpe?g|svg|webp)[^'\")]*)", html)
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
        print("   no home-page images — skipping\n")
        return
    for brand in BRANDS:
        hit = next((u for u in imgs if brand in u.lower()), None)
        if not hit:
            print(f"   – {brand}: not named in the home-page markup")
            continue
        ext = ".svg" if ".svg" in hit.lower() else ".png"
        try:
            blob = get(abs_url(hit))
        except Exception as e:
            print(f"   – {brand}: {e}")
            continue
        for page in PAGES:
            save(blob, f"{page}/assets/logos/{brand}{ext}")
        print(f"   ✓ {brand}{ext} → all three pages")
    print("   (pages reference logos/<brand>.svg — rename if you got .png)\n")


def step_candidates(imgs):
    print("3. Other home-page images → candidates/")
    n = 0
    for u in imgs:
        if any(b in u.lower() for b in BRANDS):
            continue
        name = os.path.basename(urllib.parse.urlparse(abs_url(u)).path)
        if not name:
            continue
        try:
            blob = get(abs_url(u))
        except Exception:
            continue
        if len(blob) < 8000:          # icons and sprites, not photographs
            continue
        save(blob, f"candidates/{name}")
        n += 1
        if n >= 40:
            break
    print(f"   {n} saved. Copy a lifestyle shot over each page's hero image.\n")


if __name__ == "__main__":
    if not os.path.isdir("landing"):
        sys.exit("Run this from the project root (the folder holding landing/, "
                 "advertorial/ and offer/).")
    print(f"Fetching imagery from {SHOP}\n")
    step_products()
    imgs = home_images()
    step_logos(imgs)
    step_candidates(imgs)
    print("Done. Open any page — the drawings are replaced by the photographs.")

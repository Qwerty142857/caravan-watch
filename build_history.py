"""
Store one month's listings in history/ in a condensed form.

    python build_history.py data.json 2026-10

Writes history/listings_2026-10.csv and adds (or replaces) that month in
history/months.json, which the "Past months" page (history.html) reads.

Condensed: the listing's own web link, the display price ("£49,995" -
price is kept as a number), and the scrape date (the month is the file)
are dropped. "name" is left blank when it's just make + model, and
"location" when it's just the park name, since those can be rebuilt.
Everything else - park, postcode, make, model, size, bedrooms, year,
price, site, twin flag - is kept for every listing.
"""

import csv
import json
import os
import statistics
import sys
from datetime import date

COLUMNS = ["make", "model", "name", "dimensions", "bedrooms", "year", "price",
           "park", "canonical_park", "postcode", "location", "source_site",
           "is_twin", "availability", "property_type"]

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(HERE, "history")


def as_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in ("nan", "none") else text


def condense(row):
    make, model = clean(row.get("make")), clean(row.get("model"))
    name = clean(row.get("name"))
    if name.lower() == f"{make} {model}".strip().lower():
        name = ""
    park, location = clean(row.get("park")), clean(row.get("location"))
    if location.lower() == park.lower():
        location = ""
    twin = clean(row.get("is_twin")).lower()
    return {
        "make": make, "model": model, "name": name,
        "dimensions": clean(row.get("dimensions")),
        "bedrooms": as_int(row.get("bedrooms")) or "",
        "year": as_int(row.get("year")) or "",
        "price": as_int(row.get("price_number")) or "",
        "park": park, "canonical_park": clean(row.get("canonical_park")),
        "postcode": clean(row.get("postcode")), "location": location,
        "source_site": clean(row.get("source_site")),
        "is_twin": "Y" if twin in ("true", "1", "yes", "y") else "",
        "availability": clean(row.get("availability")),
        "property_type": clean(row.get("property_type")),
    }


def summarise(month, rows, file_name, file_path):
    prices = [r["price"] for r in rows if r["price"]]
    year_of_month = int(month[:4])
    ages = [year_of_month - r["year"] for r in rows if r["year"]]
    sites = {("My Holiday Caravan" if r["source_site"].startswith("My Holiday Caravan") else r["source_site"])
             for r in rows if r["source_site"]}
    parks = {(r["canonical_park"] or r["park"]).lower() for r in rows if (r["canonical_park"] or r["park"])}
    return {
        "month": month,
        "label": date(int(month[:4]), int(month[5:7]), 1).strftime("%B %Y"),
        "file": f"history/{file_name}",
        "listings": len(rows),
        "parks": len(parks),
        "sites": len(sites),
        "median_price": int(statistics.median(prices)) if prices else None,
        "average_age": round(statistics.mean(ages), 1) if ages else None,
        "with_postcode": round(sum(1 for r in rows if r["postcode"]) / len(rows) * 100, 1) if rows else None,
        "file_kb": round(os.path.getsize(file_path) / 1024),
    }


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python build_history.py <data.json> <YYYY-MM>")
    source, month = sys.argv[1], sys.argv[2]
    if len(month) != 7 or month[4] != "-":
        sys.exit("The month must look like 2026-10")

    with open(source, encoding="utf-8") as f:
        listings = json.load(f)
    rows = [condense(r) for r in listings]
    rows.sort(key=lambda r: (r["canonical_park"] or r["park"], r["make"], r["model"], r["price"] or 0))

    os.makedirs(HISTORY_DIR, exist_ok=True)
    file_name = f"listings_{month}.csv"
    file_path = os.path.join(HISTORY_DIR, file_name)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    index_path = os.path.join(HISTORY_DIR, "months.json")
    months = []
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            months = [m for m in json.load(f) if m.get("month") != month]
    months.append(summarise(month, rows, file_name, file_path))
    months.sort(key=lambda m: m["month"], reverse=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(months, f, indent=2)

    print(f"Saved {len(rows)} listings to history/{file_name} ({months[0]['file_kb'] if months[0]['month'] == month else '?'} KB)")
    print(f"history/months.json now lists {len(months)} month(s).")


if __name__ == "__main__":
    main()

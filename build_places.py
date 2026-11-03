"""
Give every listing a county and region.

    python build_places.py data.json        (rewrites data.json in place)

website_update.py also calls add_places() each month, just before it
writes data.json.

The website works out a listing's county and region from its park's
map position (counties.json / regions.json outlines). That only works
when the listing can be matched to a park in parks.json by name, so
about one listing in ten showed no county or region. This finds a map
position for as many listings as possible, in this order:

  1. its park in parks.json - by standard park name (canonical_park),
     then by the listing's postcode, then by park name;
  2. the centre of its postcode district (postcodes.json);
  3. a town named in the advert (location, park or web address)
     that's in towns.json;
  4. a county named in the advert, set below for parks that aren't in
     the parks list (PARK_COUNTY), or for a website whose parks are all
     in one county (SITE_COUNTY).

It then tests that position against the same outlines the pages use,
so a listing's county and region match the park search and filters.
Listings with nothing to go on (e.g. "Multiple Locations") are left
blank rather than guessed.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Parks not in the parks list (or named differently), where the park's
# county is known for certain. Checked by hand, November 2026.
PARK_COUNTY = {
    "the glen caravan park": "Shropshire",              # Hillandale
    "the coppice leisure park": "Worcestershire",       # Hillandale, Wichenford WR6 6YP
    "hay-on-wye caravan park": "Powys",                 # Hillandale, HR3 5PP
    "borders hideaway holiday home park": "Powys",      # Hillandale, Clyro
    "wayside holiday park": "North Yorkshire",          # Flower of May, Pickering
    "muston grange holiday park": "North Yorkshire",    # Flower of May, Filey
    "edithmead leisure and park homes": "Somerset",     # Burnham-on-Sea
    "goulton beck lodges": "North Yorkshire",           # Eden Parks, Swainby
    "carlton miniott holiday park": "North Yorkshire",  # Thirsk
    "tydd st giles golf and country club": "Cambridgeshire",
    "docker holiday park": "Lancashire",                # Pure Leisure, LA6 1AR
    "loch ness highland retreat": "Highland",
    "bodmin holiday park": "Cornwall",
    "coldstream holiday park": "Scottish Borders",
    "newbridge country park": "Dumfries and Galloway",
    "kippford bay caravan park": "Dumfries and Galloway",
    "lagganhouse country park": "South Ayrshire",       # Ballantrae
    "middlemuir heights holiday park": "South Ayrshire",
    "highfield fisheries": "Lancashire",                # Hambleton
    "coastview shaldon": "Devon",
    "coniston view": "Cumbria",                         # Pure Leisure, Colt Park, Aldingham LA12 9RU
}
# Websites whose adverts don't name a park, but whose parks are all in one
# county: Blue Anchor Leisure sites its caravans on any of its parks, all on
# the Lincolnshire coast (owner, Nov 2026).
SITE_COUNTY = {"Blue Anchor Leisure": "Lincolnshire"}
# Parks whose name starts like this (McDonnell's "Associated Parks (Plot 13)"
# and similar): McDonnell Caravans sells only on Norfolk coast parks.
PARK_PREFIX_COUNTY = [("associated parks (plot", "Norfolk"), ("brancaster", "Norfolk")]
# Place words used in adverts that aren't a town or county name (or are
# towns missing from towns.json).
TEXT_COUNTY = {
    "whitstable": "Kent", "appleby": "Cumbria", "penrith": "Cumbria", "kings meaburn": "Cumbria",
    "haltwhistle": "Northumberland", "cottonshopeburnfoot": "Northumberland", "bishop auckland": "County Durham",
    "st asaph": "Denbighshire", "callander": "Stirling", "newtown": "Powys",
    "gower": "Swansea", "dumfries & galloway": "Dumfries and Galloway", "isle of wight": "Isle of Wight",
    "durham": "County Durham", "cotswolds": "Gloucestershire", "loch lomond": "West Dunbartonshire",
}


def _norm(text):
    return " ".join(w for w in re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).split() if w != "and")


def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _ring_dist(x, y, ring):
    best = float("inf")
    for i in range(len(ring) - 1):
        ax, ay = ring[i]
        bx, by = ring[i + 1]
        dx, dy = bx - ax, by - ay
        length = dx * dx + dy * dy
        t = 0 if length == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / length))
        best = min(best, ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) ** 0.5)
    return best


def _place(x, y, names, rings_of, bbox_of=None):
    """Same rule as the pages: inside a shape, or else the nearest one."""
    for name in names:
        b = bbox_of(name) if bbox_of else None
        if b and (x < b[0] or x > b[2] or y < b[1] or y > b[3]):
            continue
        if any(_in_ring(x, y, r) for r in rings_of(name)):
            return name
    best, best_d = None, float("inf")
    for name in names:
        for r in rings_of(name):
            d = _ring_dist(x, y, r)
            if d < best_d:
                best, best_d = name, d
    return best


class Places:
    def __init__(self, website_dir=HERE):
        load = lambda f: json.load(open(os.path.join(website_dir, f), encoding="utf-8"))
        self.regions = load("regions.json")
        self.counties = load("counties.json")
        for c in self.counties["counties"].values():
            xs = [p[0] for r in c["rings"] for p in r]
            ys = [p[1] for r in c["rings"] for p in r]
            c["bbox"] = [min(xs), min(ys), max(xs), max(ys)]
        self.county_names = {n.lower(): n for n in self.counties["order"]}
        parks = [p for p in load("parks.json")
                 if isinstance(p.get("Latitude"), (int, float)) and isinstance(p.get("Longitude"), (int, float))]
        self.park_by_name, self.park_by_pc = {}, {}
        for p in parks:
            self.park_by_name.setdefault(_norm(str(p["park_name"]).split(",")[0]), p)
            pc = str(p.get("postcode") or "").upper().replace(" ", "")
            if pc:
                self.park_by_pc.setdefault(pc, p)
        self.park_keys = list(self.park_by_name.items())
        self.districts = {d["district"]: (d["longitude"], d["latitude"]) for d in load("postcodes.json")}
        self.towns = {}
        for t in load("towns.json"):
            if isinstance(t.get("latitude"), (int, float)):
                self.towns.setdefault(t["name"].lower(), (t["longitude"], t["latitude"]))
        self._cache = {}

    # ---- outlines --------------------------------------------------------
    def county_of(self, lon, lat):
        pr = self.counties["projection"]
        x = pr["ox"] + (lon - pr["lon0"]) * pr["cos"] * pr["k"]
        y = pr["oy"] + (pr["lat1"] - lat) * pr["k"]
        c = self.counties["counties"]
        return _place(x, y, self.counties["order"], lambda n: c[n]["rings"], lambda n: c[n]["bbox"])

    def region_of(self, lon, lat):
        b = self.regions["boundaries"]
        return _place(lon, lat, self.regions["order"], lambda n: b[n])

    def county_centre(self, county):
        """lon/lat of a county's map pin (or the middle of its outline)."""
        c = self.counties["counties"][county]
        pr = self.counties["projection"]
        if c.get("pin"):
            x, y = c["pin"][0], c["pin"][1]
        else:
            x, y = (c["bbox"][0] + c["bbox"][2]) / 2, (c["bbox"][1] + c["bbox"][3]) / 2
        return (pr["lon0"] + (x - pr["ox"]) / (pr["cos"] * pr["k"]), pr["lat1"] - (y - pr["oy"]) / pr["k"])

    # ---- finding a position ---------------------------------------------
    def _find_park(self, name):
        target = _norm(str(name or "").split(",")[0])
        if not target:
            return None
        if target in self.park_by_name:
            return self.park_by_name[target]
        for key, p in self.park_keys:
            if key.startswith(target + " ") or target.startswith(key + " "):
                return p
        return None

    def position(self, row):
        """(lon, lat, how) for a listing, or (None, None, None)."""
        p = self.park_by_name.get(_norm(row.get("canonical_park"))) if row.get("canonical_park") else None
        if p is None:
            p = self.park_by_pc.get(str(row.get("postcode") or "").upper().replace(" ", ""))
        if p is None:
            p = self._find_park(row.get("park") or row.get("location"))
        if p is not None:
            return p["Longitude"], p["Latitude"], "park"
        m = re.match(r"^([A-Z]{1,2}\d[A-Z\d]?)\s*\d[A-Z]{2}$", str(row.get("postcode") or "").upper().strip())
        if m and m.group(1) in self.districts:
            return (*self.districts[m.group(1)], "postcode")
        park_text = str(row.get("park") or "").strip().lower()
        if park_text in PARK_COUNTY:
            return (*self.county_centre(PARK_COUNTY[park_text]), "county")
        for prefix, county in PARK_PREFIX_COUNTY:
            if park_text.startswith(prefix):
                return (*self.county_centre(county), "county")
        # towns named in the advert: location / park text pieces, and the town
        # at the end of a myholidayparks.com address ("...-heacham-england")
        pieces = [x.strip().lower() for x in re.split(r"[,|()]", f"{row.get('location') or ''},{row.get('park') or ''}")]
        slug = re.search(r"-([a-z-]+?)-(?:england|scotland|wales)/?$", str(row.get("listing_url") or ""))
        if slug:
            words = slug.group(1).split("-")
            pieces += [" ".join(words[-n:]) for n in (1, 2, 3) if len(words) >= n]
        for piece in pieces:
            piece = re.sub(r"^(?:nr|near)\.?\s+", "", piece)
            if piece in self.towns:
                return (*self.towns[piece], "town")
        text = " " + " ".join(pieces) + " "
        if row.get("source_site") in SITE_COUNTY:
            return (*self.county_centre(SITE_COUNTY[row["source_site"]]), "county")
        for word, county in TEXT_COUNTY.items():
            if word in text:
                return (*self.county_centre(county), "county")
        for low, county in self.county_names.items():
            if re.search(r"\b" + re.escape(low) + r"\b", text):
                return (*self.county_centre(county), "county")
        return None, None, None

    def county_region(self, row):
        lon, lat, how = self.position(row)
        if lon is None:
            return None, None, None
        key = (round(lon, 4), round(lat, 4))
        if key not in self._cache:
            self._cache[key] = (self.county_of(lon, lat), self.region_of(lon, lat))
        return (*self._cache[key], how)


def add_places(rows, website_dir=HERE):
    """Set "county" and "region" on each listing dict (None if unknown).
    Returns counts of how each was found."""
    places = Places(website_dir)
    counts = {}
    for row in rows:
        county, region, how = places.county_region(row)
        row["county"], row["region"] = county, region
        counts[how or "unknown"] = counts.get(how or "unknown", 0) + 1
    return counts


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python build_places.py data.json")
    path = sys.argv[1]
    rows = json.load(open(path, encoding="utf-8"))
    counts = add_places(rows, os.path.dirname(os.path.abspath(path)))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"County and region set for {len(rows) - counts.get('unknown', 0)} of {len(rows)} listings "
          f"({', '.join(f'{v} by {k}' for k, v in sorted(counts.items()))}).")


if __name__ == "__main__":
    main()

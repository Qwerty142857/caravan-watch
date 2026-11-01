# Static Caravan Watch – guide for Claude

A static website listing static caravans for sale across UK holiday parks, refreshed monthly.
Hosted on **GitHub Pages** from `main` of this repo (Qwerty142857/caravan-watch); publishing = merging a PR
into `main`, live within a few minutes (users may need Ctrl+F5).

## Working with the owner
- The owner is not a programmer. Explain in plain English; give Windows Command Prompt steps **one line
  at a time**, starting with `cd /d "D:\Caravan Scrapper for Drummond"`, using `py` (not `python`).
- **"Make it live"** means: open a PR and merge it. Otherwise push to the session branch and wait.
- Commit/PR messages explain *why*. Don't put model names in anything committed.

## What's in this repo (the website)
| File | Purpose |
|---|---|
| `index.html` | Home page |
| `caravans.html` | All listings (grid/map, filters, chain price comparison) – reads `data.json`, `parks.json`, `counties.json`, `regions.json` |
| `caravan.html` | One listing (`?id=…&i=<index>`) – reads `data.json`, `parks.json` |
| `compare.html` | Compare/search a caravan – reads `data.json`, `parks.json`, `counties.json`, `regions.json` |
| `map.html` | Park search by region/county/chain – reads `parks.json`, `counties.json`, `regions.json`, `towns.json`, `postcodes.json` |
| `park.html` | One park (`?park=<name>&pc=<postcode>`) – reads `parks.json`, `data.json` |
| `history.html` | "Past months" – reads `history/months.json`, links `history/listings_YYYY-MM.csv` |
| `data.json` | This month's listings (~10k rows, list of objects) |
| `parks.json` / `parks_for_website.csv` | Master parks list (3,363 parks): name, postcode, website, telephone, county, town, region, status, chain, Latitude/Longitude (json only). Keep both in step. |
| `history/` | Condensed monthly archive (Aug, Sep, Oct 2026 so far) + `months.json` summary |
| `build_history.py` | `python build_history.py data.json YYYY-MM` – adds/replaces a month in `history/` |
| `build_postcodes.py`, `build_towns.py`, `build_county_map.py` | One-off builders for the map data files |

**File formats – preserve exactly** (or the diff balloons): `parks.json` is `indent=2` with **CRLF** line
endings; `parks_for_website.csv` uses **LF**; `data.json` is `indent=2` (as written by `csv_to_json.py`:
numbers become float/int, empty → null, `is_twin` stays the string "True"/"False").

`data.json` columns: name, make, model, dimensions ("35ft x 12ft", longer first), bedrooms, year,
year_assumed ("Y" or null), location, park, postcode, availability, property_type, price_display,
price_number, source_site, date_scraped, listing_url, is_twin, canonical_park (standard park name from
the parks list).

## Where the data comes from (NOT in this repo)
The scraper lives on the owner's memory stick, `D:\Caravan Scrapper for Drummond` (a complete copy was
given to the owner as `Caravan_Watch_Complete_Nov2026.zip`, with a README). The owner runs it on Windows.
- `combined_full_scraper.py` – 45 sites built in, plus `extra_sites\` (29 site scripts run via
  `EXTRA_SITE_SCRIPTS`: Luke's 26 standalone scrapers incl. myholidayparks.com, and Thornley Leisure,
  Abbeyford Leisure, Lovat Parks via the shared `park_operator_scraper.py`). Total 74 websites.
  Harvey Longsons and Harrison use real Chrome via `nodriver`. Output:
  `combined_all_listings_<Mon>_<Year>.csv`, already cleaned by `post_process()`.
- `website_update.py <that csv>` – postcodes → `combined_all_listings_with_postcodes_<Mon>_<Year>.csv`,
  writes `website\data.json`, runs `build_history.py`. Rebuilt Oct 2026 identically to what's live.
- Failing sites save page copies to a `diagnostics\` folder – ask the owner to zip and send it.
- **This cloud environment cannot reach the scraped websites** (network allowlist). Scraper fixes are
  written blind, tested offline against saved pages/stand-ins, then run by the owner. Ask for the
  diagnostics folder rather than guessing.

## Monthly update (when the owner sends a new scrape)
1. Check per-site counts against last month (`history/months.json`, previous `data.json`); look for sites
   at 0 or sharply down, junk rows, missing fields. Fix scraper code if needed and send the owner the
   updated file(s) plus a small re-run program for just those sites.
2. Postcodes + `data.json` + archive: same steps as `website_update.py` (it can be copied in and run here
   against a checkout).
3. Test (below), commit, and publish when the owner says "make it live".

## Rules agreed with the owner
- **Duplicates** (same make, model, year, size, bedrooms, price and park on two websites): keep one copy,
  preferring the park's own operator > chain operator site (Park Holidays, Away Resorts, Discover Parks,
  Morris Leisure) > broker (Harvey Longsons, Private Sale Caravans, Ideal, Lloyds, North Wales Caravans,
  I&S Davies) > listing site (My Holiday Caravan, Parklink, Caravan4you, Parkmove, myholidayparks.com).
  Identical caravans on the **same** site are separate units and are all kept.
- Lodges, park homes and tourers are removed; homes 16ft+ wide are kept and flagged `is_twin`.
- Sold / under offer listings are left out.
- **"New"/"brand new" with no year** → current year, `year_assumed = "Y"` (from Nov 2026); shown on the
  caravan page and explained on Past months.
- Postcodes: never guess between parks sharing a name ("Seaview", "Golden Sands", "Silver Sands") unless
  the listing's location says which; leave blank instead.
- **Glass's Guide data (holiday-home trade prices/depreciation) must never be put in this repo or on the
  site** – licence restriction. Keep any such work local.

## Testing changes
```
python3 -m http.server 8765      # from the repo root, in the background
```
Load the pages with Playwright (pre-installed: `require('playwright')`, `chromium.launch()`), check for
page errors and that counts look right, at desktop and phone width (390px, no sideways scrolling).
Stop the server with `kill $(pgrep -f "[h]ttp.server 8765")` (a bare `pkill -f` matches its own shell).

## Open items (as of 1 Nov 2026)
- Apply the "new = current year" rule to all sites? (Holgates, St David's, Larkham, Wood Leisure have
  no-year "new" listings) – owner to decide.
- ~343 chain parks still link to the chain's home page rather than the park's own page.
- Owner hasn't decided on 8 suspected wrong chain assignments, 3 Haven-tagged parks not on their Haven
  list (Cardigan View, Garreg Wen, Quay West) or 3 likely duplicate park rows.
- "Abbeyford Caravan Park" (Towyn, LL22 9HN) may be Lyons' Abbeyffordd – chain left blank.
- "Robinson Crusoes Retreat Lower Largo" has a Denbighshire postcode (LL17 0LJ) but is in Fife.
- Scraper code is only on the memory stick and in the zip; owner may want it in a private repo.

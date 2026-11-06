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
| `build_places.py` | `python build_places.py data.json` – sets each listing's `county`/`region` (park → postcode district → town → county in advert; same outlines as the pages). Run by `website_update.py` |
| `build_postcodes.py`, `build_towns.py`, `build_county_map.py` | One-off builders for the map data files |

**File formats – preserve exactly** (or the diff balloons): `parks.json` is `indent=2` with **CRLF** line
endings; `parks_for_website.csv` uses **LF**; `data.json` is `indent=2` (as written by `csv_to_json.py`:
numbers become float/int, empty → null, `is_twin` stays the string "True"/"False").

`data.json` columns: name, make, model, dimensions ("35ft x 12ft", longer first), bedrooms, year,
year_assumed ("Y" or null), location, park, postcode, availability, property_type, price_display,
price_number, source_site, date_scraped, listing_url, is_twin, canonical_park (standard park name from
the parks list), county, region (from `build_places.py`; null if unknown – pages
use them when a listing can't be matched to a park by name).

## Where the data comes from (NOT in this repo)
The scraper lives on the owner's memory stick, `D:\Caravan Scrapper for Drummond` (a complete copy was
given to the owner as `Caravan_Watch_Complete_Nov2026.zip`, with a README). The owner runs it on Windows.
- `combined_full_scraper.py` – 45 sites built in, plus `extra_sites\` (29 site scripts run via
  `EXTRA_SITE_SCRIPTS`: Luke's 26 standalone scrapers incl. myholidayparks.com, and Thornley Leisure,
  Abbeyford Leisure, Lovat Parks via the shared `park_operator_scraper.py`). Total 74 websites.
  Harvey Longsons and Harrison use real Chrome via `nodriver`. Output:
  `combined_all_listings_<Mon>_<Year>.csv`, already cleaned by `post_process()`.
- `make_model_cleanup.py` (next to the scraper, called first in `post_process()`): makes → manufacturer
  only, models lose advert wording; applies the owner's `make_model_corrections.csv`
  (make,model,new_make,new_model) and saves `make_model_review.csv` (uncertain items for the owner).
- `website_update.py <that csv>` – postcodes → `combined_all_listings_with_postcodes_<Mon>_<Year>.csv`,
  adds county/region (`build_places.py`), writes `website\data.json`, runs `build_history.py`. Rebuilt Oct 2026 identically to what's live.
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
  Since Nov 2026 a final pass (`drop_lookalike_copies` in the scraper) also matches on the standard park
  name (canonical_park) + make + model + price, with year (±1) and size (±1ft) agreeing or missing; the
  kept copy takes any year/size/bedrooms/postcode only the dropped copy had.
- **Lodges (from Nov 2026):** lodges by a main manufacturer (`MAIN_LODGE_MAKERS` in the scraper) are kept,
  `property_type = "Lodge"`; bespoke lodges (no recognised make, or a no-make home 20ft+ wide) are dropped.
  Never drop a caravan just for "Lodge" in its name. Park homes and tourers are removed; homes 16ft+ wide
  are flagged `is_twin`. Lodges show mixed in with caravans; owner said hold off on a lodge filter (Nov 2026).
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

## Sources project (started 6 Nov 2026) – rely less on aggregators
Owner's aim: get listings from the operators' own websites (primary) and use aggregators only as back-up.
October 2026 analysis (`data.json`, parks matched by canonical_park / postcode / name):
- Aggregators gave ~6,700 of 10,161 listings: My Holiday Caravan 3,610, myholidayparks 1,009, Parklink 992,
  Harvey Longsons 653, Caravan4you 235, Private Sale 68 (+ brokers Ideal, Lloyds, NWC, I&S Davies, Parkmove).
- Operators NOT scraped directly, by aggregator listings: **Haven 1,734** (36 parks, almost all via MHC),
  **Parkdean 920** (55 parks, MHC), **Park Leisure 208**, Unity 58, Ladysmile 34, Leisure Resorts 24,
  Wyldecrest 22, Arden 20, Sandy Bay Preesall 19, Avon Estates 17, UK Leisure Parks 16, … ; independents
  with the most: Seal Bay Resort (cove.co.uk) 79, Whitehouse Leisure Park 63, Greenacres 37.
- **Park Holidays is scraped but incomplete**: aggregators show 1,233 more listings on its parks (Seawick
  196 vs 26 direct; 14 PH parks with no direct listings) – check `scrape_park_holidays` gets every park/page.
- ~340 cross-site double counts fixed by `drop_lookalike_copies` (Oct data now 9,852 listings).
- This cloud environment can't reach the sites; a personal environment **caravan_watch** was created
  (6 Nov 2026) allowing haven.com, parkdeanresorts.co.uk, parkholidays.com, parkleisure.co.uk, the other
  operators above and the 4 big aggregators – do the scraper building in a session on that environment.
- Plan: new operator scrapers (Haven, Parkdean, Park Leisure first) as priority 1 ("chain") sources; fix
  Park Holidays coverage; then re-measure what share still comes only from aggregators.
- **Progress 6 Nov 2026** – three standalone scrapers written and tested live (given to the owner as
  `new_operator_scrapers_Nov2026.zip`; not in this repo; each has `scrape()` returning rows in the scraper's
  column format + `run_new_operator_sites.py`). None needs a browser:
  - `haven_scraper.py`: haven.com/search-results/caravans?parkCode=XX&page=N (Next.js `self.__next_f`
    data, 15/page; park codes from the "choose a park" page). 39 parks, **1,739** listings. Pre-order models
    share one id across parks → dedupe on (park, id). MHC mirrors Haven exactly (same X… ids).
    468 of the 1,739 are such "Pre-order" catalogue models (49 models × 39 parks, ids `to-…`); MHC carried
    458 of them in Oct. **Owner decided (6 Nov): keep them all, one per park** – prices differ by park
    (e.g. Ashberry £39,995–£54,995), so they aren't treated as duplicates. No scraper change needed. Owner's own run (6 Nov) matched the test exactly.
  - `park_holidays_scraper.py`: JSON at parkholidays.com/getHolidayHomesForSale/from=N&size=100 (size 1000
    → HTTP 500). 972 homes, **882** for sale (90 Under Offer dropped) vs 746 in Oct. Includes the Park
    Leisure parks. Title "Make Model Year" (multi-word makes listed in the script; one title says "undefined").
  - `park_leisure_scraper.py`: parkleisure.co.uk persisted GraphQL (`Items`/`GetLocationData`, header
    `x-phuk-stack: parkleisure`); 10 parks, 140 for sale. Back-up only – same stock is on parkholidays.com.
  - **Park Holidays "gap" was mostly aggregator mis-assignment**, not missed listings: e.g. myholidayparks
    put 169 Clacton-area homes at Seawick (Seawick really has 28). Treat myholidayparks park names with care.
  - **Parkdean**: Cloudflare "Just a moment" challenge – not scraped; keep MHC for Parkdean (don't try to get
    round the challenge).
  - Environment now also allows the bare domains the smaller operators redirect to (unityholidays.co.uk,
    ladysmile.co.uk, leisureresorts.co.uk, wyldecrestholidayparks.co.uk, ardenparks.co.uk,
    sandybaypreesall.co.uk, avon-estates.co.uk, ukleisureparks.co.uk, cove.co.uk, sfparks.co.uk –
    Whitehouse Leisure Park is now under sfparks.co.uk).
  - **`small_operators_scraper.py`** (6 Nov, tested live, ~297 listings): Unity 73 (WP `/ownership/holiday-homes/
    all-stock/` cards carry `data-item-meta` JSON; homes with no park tag → park from the sales phone on the
    detail page), Ladysmile 16 (WP REST `holidayhomesforsale` acf; `which_park` lm/oak/sold; free-text sizes),
    Wyldecrest 58 (REST `holiday-homes` list + each detail page for price/size), Arden 15 (WooCommerce Store
    API; holiday-park categories only, residential/park homes skipped), Avon Estates 14 (`/holiday-home-search/`
    `property-card` classes; 3 lodges tagged "Firefly Fields" but under Dovecote's pages – postcode left
    blank), UK Leisure Parks 56 (REST `sale` acf: price, size, beds, sale_option; few years), Seal Bay 23
    (cove.co.uk list page), SF Parks 42 (park-specific only via `?site=sgg|whlp|sbcp|sunvalley&ppp=-1`;
    the other ~98 are North Wales Caravans stock "on a range of parks", left to the NWC scraper).
    Skipped: Leisure Resorts (only "from £X" ranges), Sandy Bay Preesall (no prices published).
  - Aggregator park assignment again looks loose: MHC put 63 at Whitehouse (SF Parks has 4 there), and
    Seal Bay 66 on aggregators vs 23 on its own site.
  - Owner's full run of all new scrapers (6 Nov): 2,917 rows, matches the tests (Haven 1,738 – one sold since).
  - **Wired in (6 Nov, `scraper_update_Nov2026.zip`)**: `combined_full_scraper.py` gets
    `OPERATOR_SITE_SCRIPTS` / `_run_operator_site()` (imports haven/park_holidays/small_operators scripts from
    `extra_sites\` and calls their functions – no CSV), run before Track 1; Track 1's "Park Holidays" entry now
    uses `park_holidays_scraper.py` (old `scrape_parkholidays` asked for "Static Caravan" type only – missed
    ~130 Villas + lodges – and kept Under Offer; left in the file unused); "Haven"/"Park Leisure" added to
    `CHAIN_OPERATOR_SOURCES`; new `drop_mhc_copies_of_haven()` (MHC link ends in Haven's stock number; `to-…`
    pre-order ids must also match park) runs before `drop_lookalike_copies`; post_process now drops rows whose
    `availability` says Sold/Reserved/Under offer (Oct live data had 130: Parklink 111). Only 3 original lines
    changed. Test: post_process on Oct data.json (minus PH) + owner's 6 Nov new-site CSV → 12,023 in, 9,519 out;
    every new-source row kept except bespoke lodges. (Test ran without `make_model_cleanup.py`, not available here.)
  - **Next:** owner installs the update and runs a full month; then re-measure the aggregator share.

## Open items (as of 1 Nov 2026)
- Apply the "new = current year" rule to all sites? (Holgates, St David's, Larkham, Wood Leisure have
  no-year "new" listings) – owner to decide.
- ~343 chain parks still link to the chain's home page rather than the park's own page.
- Owner hasn't decided on 8 suspected wrong chain assignments, 3 Haven-tagged parks not on their Haven
  list (Cardigan View, Garreg Wen, Quay West) or 3 likely duplicate park rows.
- "Abbeyford Caravan Park" (Towyn, LL22 9HN) may be Lyons' Abbeyffordd – chain left blank.
- "Robinson Crusoes Retreat Lower Largo" has a Denbighshire postcode (LL17 0LJ) but is in Fife.
- Scraper code is only on the memory stick and in the zip; owner may want it in a private repo.

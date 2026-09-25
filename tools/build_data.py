"""Builds data.json: Summer 2027 internships from public listings and company job boards."""
import concurrent.futures as cf
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SIMPLIFY = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
MUSE = "https://www.themuse.com/api/public/jobs"
# The Muse's internship categories, minus Healthcare (thousands of pharmacy and clinical rotations).
MUSE_CATEGORIES = ["Business Operations", "Sales", "Product Management", "Project Management", "Data and Analytics",
    "Advertising and Marketing", "Account Management", "Human Resources and Recruitment", "Management",
    "Accounting and Finance", "Media, PR, and Communications", "Writing and Editing", "Legal Services", "Retail",
    "Education", "Computer and IT", "Real Estate", "Transportation and Logistics", "Administration and Office",
    "Software Engineering", "Design and UX", "Science and Engineering", "Arts", "Unknown"]
SIZES_FILE = os.path.join(os.path.dirname(__file__), "company_sizes.json")

GREENHOUSE = """airbnb stripe robinhood coinbase doordashusa pinterest reddit dropbox figma discord lyft instacart
gusto brex samsara databricks twilio okta toast squarespace duolingo peloton warbyparker chime affirm sofi
nerdwallet roblox riotgames epicgames twitch cloudflare datadog mongodb elastic asana gitlab pagerduty scaleai
andurilindustries flexport faire whatnot benchling carta webflow airtable calendly zocdoc nuro waymo
appliedintuition gemini opendoor wayfair etsy mercury lattice vercel amplitude fivetran confluent clickup
navan betterment wealthfront marqeta checkr gong attentive klaviyo braze zendesk intercom
anthropic adyen block hellofresh justworks oscar oura prizepicks stockx upstart scopely nextdoor sweetgreen
glossier everlane ripple""".split()
LEVER = "palantir shieldai spotify whoop lyrahealth greenlight zoox gopuff ro jamcity".split()
ASHBY = """ramp notion openai linear retool deel clay posthog replit supabase plaid cohere elevenlabs harvey
perplexity sierra vanta wealthsimple sleeper supercell substack modal drata headway thumbtack strava poshmark
hopper oyster patreon acorns zapier kayak""".split()
# (display name, host, tenant, site)
WORKDAY = [
    ("Visa", "visa.wd5", "visa", "Visa_Early_Careers"),
    ("PIMCO", "pimco.wd1", "pimco", "pimco-careers"),
    ("PwC", "pwc.wd3", "pwc", "US_Entry_Level_Careers"),
    ("Salesforce", "salesforce.wd12", "salesforce", "External_Career_Site"),
    ("Adobe", "adobe.wd5", "adobe", "external_experienced"),
    ("NVIDIA", "nvidia.wd5", "nvidia", "NVIDIAExternalCareerSite"),
    ("Target", "target.wd5", "target", "targetcareers"),
    ("Walmart", "walmart.wd5", "walmart", "WalmartExternal"),
    ("Capital One", "capitalone.wd12", "capitalone", "Capital_One"),
    ("Mastercard", "mastercard.wd1", "mastercard", "CorporateCareers"),
    ("PayPal", "paypal.wd1", "paypal", "jobs"),
    ("Intel", "intel.wd1", "intel", "External"),
    ("Disney", "disney.wd5", "disney", "disneycareer"),
    ("Nike", "nike.wd1", "nike", "nke"),
    ("Autodesk", "autodesk.wd1", "autodesk", "uni"),
    ("Workday", "workday.wd5", "workday", "Workday_Early_Career"),
    ("Levi Strauss & Co.", "levistraussandco.wd5", "levistraussandco", "External"),
    ("Illumina", "illumina.wd1", "illumina", "illumina-careers"),
    ("Zurn Elkay", "elkay.wd1", "elkay", "Elkay_External"),
    ("Trimble", "trimble.wd1", "trimble", "TrimbleCareers"),
    ("U.S. Bank", "usbank.wd1", "usbank", "US_Bank_Careers"),
    ("USAA", "usaa.wd1", "usaa", "USAAJOBSWD"),
    ("Dick's Sporting Goods", "dickssportinggoods.wd1", "dickssportinggoods", "DSG"),
]

ALIASES = {"SF": "San Francisco, CA", "LA": "Los Angeles, CA", "NYC": "New York, NY"}
# Banks and consultancies call their interns "summer analysts" or "summer associates", so those count too.
INTERN = re.compile(r"\bintern(ship)?s?\b|\bsummer (analyst|associate|scholar|fellow)s?\b|\bapprentice(ship)?s?\b", re.I)
OTHER_TERM = re.compile(r"\b(2025|2026|2028|fall|autumn|spring|winter|co-?op|jan(uary)?|feb(ruary)?|march|oct(ober)?|nov(ember)?|dec(ember)?)\b", re.I)
SUMMER_27 = re.compile(r"summer\s*('|20)?27|2027\s*summer", re.I)
CUTOFF = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
# Simplify's headcount is wrong or missing for some big employers with many listings.
BIG = "10,001+"
SIZE_OVERRIDES = {n: BIG for n in ["Trimble", "Mastercard", "Tokyo Electron", "Teledyne", "GE Healthcare",
    "Fidelity National Information Services", "Enterprise Mobility", "JPMorgan Chase", "The TJX Companies, Inc.",
    "Spectrum", "NIKE, Inc.", "Nike", "Southern California Edison (SCE)", "Grainger", "PNC", "Eaton", "The Hartford",
    "CRH", "Philips", "BD", "Liberty Mutual Insurance", "Pilot Company", "Warner Bros. Discovery",
    "Navy Federal Credit Union", "Entergy", "Regions Bank", "Levi Strauss & Co.", "Cadence",
    "Sandia National Laboratories", "HelloFresh", "DoorDash USA"]}
SIZE_OVERRIDES.update({"Altria Group, Inc.": "5,001-10,000", "HNTB": "5,001-10,000", "W.R. Berkley": "5,001-10,000",
    "Genworth Financial": "1,001-5,000", "Lazard": "1,001-5,000", "PGIM": "1,001-5,000", "Zurn Elkay": "1,001-5,000",
    "Anduril Industries": "1,001-5,000", "Samsara Inc.": "1,001-5,000", "Excellus BCBS": "1,001-5,000",
    "Gallup": "1,001-5,000", "The Aerospace Corporation": "1,001-5,000", "QTS": "1,001-5,000",
    "Akuna Capital University": "201-500", "Kairos Power": "201-500", "Shieldai": "501-1,000"})
SIZE_BUCKET = {"1-10": "s", "11-50": "s", "51-200": "s", "201-500": "m", "501-1,000": "m", "1,001-5,000": "m",
    "5,001-10,000": "l", "10,001+": "l"}

CATEGORIES = [
    ("Quant", r"\bquant|trading\b|trader"),
    ("Product", r"product manag|product strateg|product owner|product operations|product analyst|\bapm\b|associate product"),
    ("Hardware", r"hardware|electrical|mechanical|manufacturing|embedded|firmware|robotic|aerospace|avionic|asic|fpga|silicon|mixed signal|analog|circuit|chip"),
    ("AI/ML/Data", r"machine learning|\bml\b|\bai\b|data|analytics|research scien|applied scien"),
    ("Software", r"software|developer|engineer|\bswe\b|frontend|backend|full.?stack|mobile|\bios\b|android|infrastructure|security|devops|\bsre\b|programmer"),
    ("Design", r"design|\bux\b|creative|illustrat"),
]

STATE_NAMES = {"alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID", "illinois": "IL",
    "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC"}
CODES = set(STATE_NAMES.values())
CITY_ONLY = {"new york": "New York, NY", "new york city": "New York, NY", "san francisco": "San Francisco, CA",
    "los angeles": "Los Angeles, CA", "seattle": "Seattle, WA", "chicago": "Chicago, IL", "boston": "Boston, MA",
    "austin": "Austin, TX", "atlanta": "Atlanta, GA", "washington dc": "Washington, DC", "washington, dc": "Washington, DC"}


def clean_location(p):
    p = re.sub(r"\s*,\s*", ", ", p.strip().strip(",")).strip()
    p = re.sub(r"^(hybrid|on-?site|in office)\s*[-:]\s*", "", p, flags=re.I)
    p = re.sub(r"^(US|USA|United States)\s*[-,]\s*", "", p)
    p = re.sub(r",?\s*\b(US|USA|United States( of America)?)$", "", p).strip()
    m = re.match(r"^([A-Za-z ]+?)\s+-\s+(.+)$", p)
    if m and m.group(1).lower() in STATE_NAMES:
        return m.group(2) + ", " + STATE_NAMES[m.group(1).lower()]
    if re.match(r"^\d+ Locations$", p):
        return "Multiple locations"
    m = re.match(r"^([A-Za-z ]+), (.+)$", p)
    if m and (m.group(1) in CODES or m.group(1).lower() in STATE_NAMES) and "," not in m.group(2) and m.group(2) not in CODES:
        code = m.group(1) if m.group(1) in CODES else STATE_NAMES[m.group(1).lower()]
        return m.group(2) + ", " + code
    if p.lower() in CITY_ONLY:
        return CITY_ONLY[p.lower()]
    m = re.match(r"^([A-Z]{2})\s*-\s*(.+)$", p)
    if m and m.group(1) in CODES:
        return m.group(2) + ", " + m.group(1)
    m = re.match(r"^([A-Z]{2}), (.+)$", p)
    if m and m.group(1) in CODES:
        return m.group(2) + ", " + m.group(1)
    m = re.match(r"^(.+), ([A-Za-z ]+)$", p)
    if m and m.group(2).lower() in STATE_NAMES:
        return m.group(1) + ", " + STATE_NAMES[m.group(2).lower()]
    return ALIASES.get(p, p)


def degrees(title):
    t = title.lower()
    out = []
    if re.search(r"\bbs\b|\bba\b|bachelor|undergrad", t): out.append("Bachelor's")
    if re.search(r"\bms\b|master", t): out.append("Master's")
    if "mba" in t: out.append("MBA")
    if "phd" in t or "ph.d" in t: out.append("PhD")
    return out


def get_json(url, body=None, timeout=20):
    headers = {"User-Agent": "Mozilla/5.0 (internship-sweeper)", "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return None


def category(title):
    for name, pat in CATEGORIES:
        if re.search(pat, title, re.I):
            return name
    return "Business"


def is_summer_2027(title, posted):
    if not INTERN.search(title):
        return False
    if SUMMER_27.search(title):
        return not re.search(r"\b(2025|2026|2028)\b", title)
    if OTHER_TERM.search(title):
        return False
    return posted >= CUTOFF


def split_locations(text):
    if not text:
        return []
    out = []
    for p in re.split(r";|\||/|•| or ", text):
        p = clean_location(p)
        if p and p not in out:
            out.append(p)
    return out


def row(company, title, locs, url, posted, source):
    return {"c": company, "t": title.strip(), "l": locs, "u": url, "d": int(posted), "a": 1,
            "g": category(title), "deg": degrees(title), "s": source}


def iso_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return time.time()


def from_greenhouse(token):
    meta = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}")
    jobs = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs")
    if not jobs:
        return []
    name = (meta or {}).get("name") or token.title()
    out = []
    for j in jobs.get("jobs", []):
        posted = iso_ts(j.get("first_published") or j.get("updated_at") or "")
        if is_summer_2027(j["title"], posted):
            out.append(row(name, j["title"], split_locations((j.get("location") or {}).get("name")),
                           j["absolute_url"], posted, "company"))
    return out


def from_lever(token):
    jobs = get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    if not isinstance(jobs, list):
        return []
    out = []
    for j in jobs:
        posted = (j.get("createdAt") or time.time() * 1000) / 1000
        cats = j.get("categories") or {}
        locs = cats.get("allLocations") or [cats.get("location")]
        if is_summer_2027(j["text"], posted):
            out.append(row(token.title(), j["text"], split_locations("; ".join(l for l in locs if l)),
                           j["hostedUrl"], posted, "company"))
    return out


def from_ashby(token):
    d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
    if not d or "jobs" not in d:
        return []
    out = []
    for j in d["jobs"]:
        posted = iso_ts(j.get("publishedAt") or "")
        locs = [j.get("location")] + [s.get("location") for s in j.get("secondaryLocations") or []]
        if is_summer_2027(j["title"], posted):
            out.append(row(token.title(), j["title"], split_locations("; ".join(l for l in locs if l)),
                           j["jobUrl"], posted, "company"))
    return out


def workday_posted(text):
    now = time.time()
    t = (text or "").lower()
    if "today" in t:
        return now
    if "yesterday" in t:
        return now - 86400
    m = re.search(r"(\d+)", t)
    return now - int(m.group(1)) * 86400 if m else now - 30 * 86400


def from_workday(entry):
    name, host, tenant, site = entry
    base = f"https://{host}.myworkdayjobs.com"
    out = []
    for offset in range(0, 200, 20):
        d = get_json(f"{base}/wday/cxs/{tenant}/{site}/jobs",
                     {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": "intern"})
        if not d or not d.get("jobPostings"):
            break
        for j in d["jobPostings"]:
            posted = workday_posted(j.get("postedOn"))
            if is_summer_2027(j.get("title", ""), posted):
                out.append(row(name, j["title"], split_locations(j.get("locationsText", "")),
                               f"{base}/en-US/{site}{j['externalPath']}", posted, "company"))
        if offset + 20 >= d.get("total", 0):
            break
    return out


def from_simplify():
    rows = []
    for x in get_json(SIMPLIFY, timeout=60) or []:
        if not x.get("is_visible", True):
            continue
        terms = x.get("terms") or ["N/A"]
        # Undated listings count when the title and posting date say Summer 2027.
        if "Summer 2027" not in terms and not (terms == ["N/A"] and is_summer_2027(x["title"], x["date_posted"])):
            continue
        rows.append({
            "c": x["company_name"], "t": x["title"],
            "l": [ALIASES.get(l, l) for l in x.get("locations", [])],
            "u": x["url"], "d": x["date_posted"], "a": 1 if x.get("active") else 0,
            "g": "Software" if x.get("category") == "Software Engineering" else x.get("category", ""),
            "deg": x.get("degrees", []), "s": "tracker",
            "_slug": (x.get("company_url") or "").rsplit("/c/", 1)[-1] or None,
        })
    return rows


def muse_page(cat, page):
    q = urllib.parse.urlencode({"level": "Internship", "category": cat, "page": page})
    return get_json(f"{MUSE}?{q}")


def from_muse(cat):
    out = []
    first = muse_page(cat, 0)
    if not first:
        return out
    pages = [first] + [muse_page(cat, p) for p in range(1, min(first.get("page_count", 1), 99))]
    for d in pages:
        for j in (d or {}).get("results", []):
            posted = iso_ts(j.get("publication_date") or "")
            if is_summer_2027(j.get("name", ""), posted):
                locs = split_locations("; ".join(l["name"] for l in j.get("locations", [])))
                out.append(row(j["company"]["name"], j["name"], locs, j["refs"]["landing_page"], posted, "muse"))
    return out


def simplify_size(slug):
    """Headcount band from the company's public Simplify page, e.g. "1,001-5,000", or None."""
    url = "https://simplify.jobs/c/" + urllib.parse.quote(slug)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (internship-sweeper)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return None
    m = re.search(r"companySize=([^\"&]+)", html)
    return urllib.parse.unquote_plus(m.group(1)).replace(" employees", "") if m else None


def add_sizes(rows):
    """Tags each row with s/m/l. Sizes are cached in company_sizes.json; misses are retried after 30 days."""
    try:
        cache = json.load(open(SIZES_FILE))
    except Exception:
        cache = {}
    now = time.time()
    slugs = {}
    for r in rows:
        slugs.setdefault(r["c"], r.pop("_slug", None) or re.sub(r"[^A-Za-z0-9]+", "-", r["c"]).strip("-"))
    todo = [c for c in slugs if c not in SIZE_OVERRIDES and (c not in cache or (not cache[c]["size"] and now - cache[c]["checked"] > 30 * 86400))]
    with cf.ThreadPoolExecutor(8) as ex:
        for c, size in zip(todo, ex.map(lambda c: simplify_size(slugs[c]), todo)):
            cache[c] = {"size": size, "checked": int(now)}
    with open(SIZES_FILE, "w") as f:
        json.dump(dict(sorted(cache.items())), f, indent=0)
    for r in rows:
        z = SIZE_BUCKET.get(SIZE_OVERRIDES.get(r["c"]) or (cache.get(r["c"]) or {}).get("size") or "")
        if z:
            r["z"] = z
    return len(todo)


def key(r):
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    return norm(r["c"])[:12] + "|" + norm(re.sub(r"\(.*?\)|summer|2027|intern(ship)?", "", r["t"], flags=re.I))


def main():
    rows = from_simplify()
    if not rows:
        raise SystemExit("tracker download failed; keeping the old data.json")
    seen = {key(r) for r in rows}
    jobs = ([(from_greenhouse, t) for t in GREENHOUSE] + [(from_lever, t) for t in LEVER] +
            [(from_ashby, t) for t in ASHBY] + [(from_workday, w) for w in WORKDAY] +
            [(from_muse, c) for c in MUSE_CATEGORIES])
    added = 0
    with cf.ThreadPoolExecutor(24) as ex:
        for found in ex.map(lambda j: j[0](j[1]), jobs):
            for r in found:
                k = key(r)
                if k not in seen:
                    seen.add(k)
                    rows.append(r)
                    added += 1
    unique = {}
    for r in rows:
        k = (r["c"].lower(), r["t"].lower().strip(), tuple(sorted(r["l"])))
        if k not in unique or (r["a"] and not unique[k]["a"]):
            unique[k] = r
    rows = sorted(unique.values(), key=lambda r: -r["d"])
    looked_up = add_sizes(rows)
    with open("data.json", "w") as f:
        json.dump(rows, f, separators=(",", ":"))
    print(len(rows), "listings,", added, "added from company job boards and The Muse,",
          sum("z" in r for r in rows), "with a company size,", looked_up, "sizes looked up")


if __name__ == "__main__":
    main()

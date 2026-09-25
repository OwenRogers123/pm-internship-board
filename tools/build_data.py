import json, urllib.request

SRC = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
ALIASES = {"SF": "San Francisco, CA", "LA": "Los Angeles, CA", "NYC": "New York, NY"}

with urllib.request.urlopen(SRC) as r:
    listings = json.load(r)

rows = []
for x in listings:
    if "Summer 2027" not in x.get("terms", []) or not x.get("is_visible", True):
        continue
    rows.append({
        "c": x["company_name"],
        "t": x["title"],
        "l": [ALIASES.get(l, l) for l in x.get("locations", [])],
        "u": x["url"],
        "d": x["date_posted"],
        "a": 1 if x.get("active") else 0,
        "g": "Software" if x.get("category") == "Software Engineering" else x.get("category", ""),
        "deg": x.get("degrees", []),
    })
rows.sort(key=lambda r: -r["d"])

with open("data.json", "w") as f:
    json.dump(rows, f, separators=(",", ":"))
print(len(rows), "listings")

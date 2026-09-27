# Internship Sweeper

**Live:** https://owenrogers123.github.io/pm-internship-board/

Search Summer 2027 internships from job boards and company career pages, filtered by major, location, degree, company size and posting date.

## Where the listings come from

About 4,300 listings come from the [SimplifyJobs](https://github.com/SimplifyJobs/Summer2027-Internships) list, [The Muse](https://www.themuse.com/developers/api/v2), and the public job boards of about 150 companies (Greenhouse, Lever, Ashby and Workday). A GitHub Action rebuilds the list every day with `tools/build_data.py`. Company size comes from each company's Simplify profile, with a short list of corrections in the same file.

The build also cleans the data:

- Drops year-round, part-time, new grad and full-time roles that trackers file under Summer 2027
- Tags each listing as product, business, software, data, hardware, quant, design or other from its title
- Tags law (JD) postings so they don't show up for undergrads
- Merges the same job listed once per city, or on two boards, into one listing with every city

Coverage is strongest for business, tech, finance, engineering and design. Nursing, teaching, journalism and most healthcare roles aren't covered yet.

## Search

- Nothing shows until you type a role or pick a filter
- Loose matching: "product" also finds product manager, product strategy and APM roles, and "sales" also finds business development and account executive roles
- Handles typos ("accountng", "sofware enginer") and ignores filler words like "internship"
- Best matches first, with the matched words highlighted. Master's- and PhD-only postings rank a little lower unless you pick a degree
- US listings by default, with an option to include roles abroad
- Degree options also keep postings that don't state a degree, since most don't
- When nothing matches, it says which filter to remove and how many results that brings back
- Every search is saved in the URL, so it can be shared
- One click runs the same search on Indeed, LinkedIn, Wellfound, Handshake and Google Jobs, which block scripts from pulling their listings

## Stack

One static HTML file and one JSON file, no backend, hosted on GitHub Pages.

---
Built by Owen Rogers (Cal Poly, Business Administration + Information Systems) for Build Day #1.

# PM Internship Board

**Live:** https://owenrogers123.github.io/pm-internship-board/

A live tracker for my own Summer 2027 product-management internship search, filtered to California roles that don't require a CS/engineering degree — built because manually re-checking 40+ company career pages every week for one line of eligibility text is exactly the kind of chore that eats a Tuesday night.

## What it does

- **Window chart** — every live/expected role plotted against its application window, with a today-marker so it's obvious what's closing soon.
- **Open now** — ranked list of live roles, apply links, and the exact eligibility text that got each one in (or would have kept it out).
- **Checked, and what it cost** — every company ruled out and why, so a future sweep never re-checks a dead end (a closed req, an MBA-only track, a hard CS-degree bar) and burns time re-discovering something already known.
- **Prep work** — a checklist for the stuff that actually gates an application (resume rewrite, product teardowns, portfolio).
- Checkbox state (applied / prep done) saves to your own browser's local storage.

## How it stays current

A recurring AI agent sweep (Claude, on a 2-day schedule) does the actual research:

1. Pulls the community-maintained [SimplifyJobs/Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships) tracker and filters to product-track roles in California.
2. Runs a general web/LinkedIn search for anything the tracker missed.
3. Spot-checks every role already on the board for still-live status — a role can vanish or tighten its eligibility text between sweeps.
4. Checks a fixed watchlist of ~40 California-headquartered companies directly against their own career boards.
5. Cross-references every find against a corrections log of things that turned out wrong before (a role that looked open but had already closed, a "PM internship" that was actually a full-time rotational program, etc.) so the same mistake never gets made twice.

The results get written to this page and to a parallel markdown archive (tracker files + a corrections log), so the reasoning behind every decision — not just the current state — survives from one sweep to the next.

## Stack

Static HTML/CSS/JS, no build step, no backend. Deployed on GitHub Pages. The research/update loop runs as a Claude scheduled task against local markdown files and this page's source.

---
Built by Owen Rogers (Cal Poly, Business Administration + Information Systems) for [Build Day #1](https://forms.gle/FLURyTn59ieRF1i4A).

# Internship Sweeper

**Live:** https://owenrogers123.github.io/pm-internship-board/

Every Summer 2027 product management internship I can actually apply to as a Cal Poly business major, found and filtered automatically.

## The problem

Most PM internships quietly require a computer science degree. Finding the ones that don't means opening dozens of career pages every week and reading the fine print on each one. It takes hours, and postings close or change without warning.

## How it works

An AI agent (Claude, running on a schedule every two days) does the checking:

1. **Scan.** Searches the web: job boards, LinkedIn, Google, and about 40 California company career pages.
2. **Filter.** Opens each posting and reads the real requirements. A role only makes the list if it is in California, doesn't require a CS or engineering degree, and is real product work.
3. **Update.** Rewrites this page, emails me the results every 2 days, and keeps a log of past mistakes, so a closed or wrong role never shows up twice.

## Features

- Countdown for every role with a hard deadline
- Search, plus filters for closing soon, new this week, and not applied yet
- Closed roles are marked automatically once their deadline passes
- "Ruled out" list showing every rejected company and why
- "Applied" and prep checkboxes that save in your browser

## Search

Anyone can search every Summer 2027 internship by keyword, major, location, degree and posting date. About 3,000 listings come from the [SimplifyJobs](https://github.com/SimplifyJobs/Summer2027-Internships) list plus the public job boards of about 100 companies (Greenhouse, Lever, Ashby and Workday), refreshed every day by a GitHub Action.

- Loose matching: "product" also finds product manager, product strategy and APM roles, and "sales" also finds business development and account executive roles
- Handles typos ("accountng", "sofware enginer") and ignores filler words like "internship"
- Best matches first, with the matched words highlighted
- When nothing matches, it says which filter to remove and how many results that brings back
- Every search is saved in the URL, so it can be shared

## Stack

One static HTML file with no build step and no backend, hosted on GitHub Pages.

---
Built by Owen Rogers (Cal Poly, Business Administration + Information Systems) for Build Day #1.

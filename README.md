from pathlib import Path

content = """# Subdomain Finder

**Subdomain Finder** is a Python-based reconnaissance tool that combines multiple discovery techniques — **BeautifulSoup scraping**, **Selenium JavaScript rendering**, **DNS verification**, and **brute-force enumeration** — to find subdomains of a target domain efficiently.

> **New:** The script now prints validated subdomains to the console **and** can write them to a newline-separated output file using the `--output` option.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [How it works (Workflow)](#how-it-works-workflow)
- [Usage Examples](#usage-examples)
- [Arguments / Flags](#arguments--flags)
- [Output](#output)
- [Function Reference](#function-reference)
- [Notes & Improvements](#notes--improvements)
- [Legal / Ethics](#legal--ethics)
- [License](#license)

---

## Features

- ✅ Extracts links from static pages using `requests` + `BeautifulSoup`.
- ✅ Uses Selenium to render JavaScript-heavy pages and capture dynamically generated links.
- ✅ Parses `sitemap.xml` for additional URLs.
- ✅ Performs passive discovery via `crt.sh` (optional).
- ✅ Brute-forces subdomains from a wordlist with multithreading.
- ✅ Validates candidates with DNS (A/AAAA) and HTTP checks.
- ✅ Prints results and optionally writes validated subdomains to an output file.

---

## Requirements

- Python 3.8+ (3.9+ recommended)
- Chrome browser (if using Selenium + ChromeDriver)
- The following Python packages:
  - `requests`
  - `beautifulsoup4`
  - `tldextract`
  - `dnspython` (optional but recommended)
  - `selenium`
  - `webdriver-manager`

---

## Installation

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\\Scripts\\Activate.ps1
Install dependencies:

bash
Always show details

Copy code
python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 tldextract dnspython selenium webdriver-manager
How it works (Workflow)
vbnet
Always show details

Copy code
User provides domain
       ↓
 Parse sitemap.xml (if present) ──► Harvest URLs
       ↓
Requests + BeautifulSoup (static pages) ──► Extracted href links
       ↓
Selenium (optional, JS-rendered pages) ──► Extra links
       ↓
crt.sh passive lookup (optional) ──► Passive subdomain candidates
       ↓
Brute-force from wordlist (threads) ──► Generated candidates
       ↓
DNS resolution + HTTP checks ──► Final validated subdomains
       ↓
Print to console and optional file output
Usage Examples
Basic scan (no brute-force, no Selenium):

bash
Always show details

Copy code
python subfinder_combined.py example.com
Scan with brute-force and Selenium:

bash
Always show details

Copy code
python subfinder_combined.py example.com --wordlist subdomains.txt --selenium
Include crt.sh passive discovery and save results to file:

bash
Always show details

Copy code
python subfinder_combined.py example.com --crt --wordlist subdomains.txt --output found_subs.txt
Verbose debug mode (see more logging and run Selenium non-headless):

bash
Always show details

Copy code
python subfinder_combined.py example.com --selenium --debug --verbose
Arguments / Flags
domain (positional) — Root domain to scan (e.g., example.com).

--wordlist, -w — Path to a newline-separated subdomain wordlist for brute-forcing.

--threads, -t — Number of threads for brute forcing (default: 40).

--sleep — Optional delay (seconds) between brute-force checks (throttling).

--selenium — Enable Selenium for JavaScript rendering (heavier).

--crt — Enable passive discovery via crt.sh.

--max-pages — Max pages Selenium will render/crawl (default: 10).

--verbose — Print failed verification attempts (helpful for debugging).

--debug — Run Selenium in non-headless mode to debug rendering issues.

--output, -o — Write final validated subdomains to a file (one per line).

Output
Console: final validated subdomains are printed to stdout.

File: if --output found_subs.txt is used, the script writes one hostname per line to found_subs.txt. The file is overwritten if it exists.

Example found_subs.txt:

Always show details

Copy code
api.example.com
blog.example.com
shop.example.com
Function Reference (brief)
get_selenium_driver(headless=True, window_size=(1200, 800))
Returns a configured Selenium Chrome WebDriver. Use headless=False for debugging.

fetch_html_requests(url, timeout=5)
Fetch page HTML using requests. Fast for static content.

fetch_html_selenium(driver, url, wait=2)
Open a page with Selenium and return the rendered page_source.

extract_links_from_html(html, base_url)
Parse <a href> links using BeautifulSoup and normalize to absolute URLs.

parse_sitemap(domain)
Attempts to fetch https://domain/sitemap.xml and return <loc> entries.

subdomain_from_hostname(hostname, root_domain)
Uses tldextract to extract subdomain part for hostnames under root_domain.

dns_resolves(host)
Uses dnspython to check A/AAAA records for a host.

http_check(host, protocols=("https","http"))
Performs HEAD (with GET fallback) to check if a host responds.

harvest_with_requests(domain, start_paths=None)
Harvest links from seed pages using requests + BeautifulSoup.

harvest_with_selenium(domain, driver, seeds=None, max_pages=10)
Harvest links from JS-rendered pages using Selenium.

crtsh_lookup(domain)
Query crt.sh JSON endpoint to extract subdomains from certificate transparency logs.

brute_force_check(domain, wordlist_path, threads=30, rate_sleep=0.0)
Brute-force common subdomains from a wordlist using threads.

aggregate_and_filter(found_hosts, root_domain)
Normalize and filter discovered hosts to only include the target domain.

main(args)
Orchestrates the entire pipeline and handles printing + optional file output.

Notes & Improvements
Wildcard DNS: Some domains resolve any subdomain due to wildcard DNS. Consider adding a wildcard detection step (resolve a random subdomain to see if it resolves).

Politeness: Be conservative with --threads and use --sleep when scanning external targets.

Selenium: Only enable Selenium when necessary — it is resource-heavy.

Persistence: For long brute-force runs, implement checkpointing to resume.

Passive APIs: Consider adding SecurityTrails / Censys API integrations (these require API keys and handle rate limits).

Legal / Ethics
This tool is provided for educational and authorized security testing only. Always obtain explicit permission before scanning domains you do not own. Unauthorized scanning may be illegal in your jurisdiction.

License
MIT License — use responsibly.

Author: Preetinder Singh
Version: 1.1
"""

readme_path = Path("/mnt/data/README_Subdomain_Finder_Updated.md")
readme_path.write_text(content, encoding="utf-8")
readme_path

Always show details

Copy code
Result
PosixPath('/mnt/data/README_Subdomain_Finder_Updated.md')

# Subdomain Finder

A Python-based reconnaissance tool that discovers subdomains of a target domain using multiple complementary techniques: **BeautifulSoup** scraping, **Selenium** (for JS-rendered pages), **DNS lookups**, **crt.sh** passive discovery, and **wordlist brute-forcing**.  
This updated version includes an `--output` option to save validated subdomains to a newline-separated text file.

---

## Quick description

**Subdomain Finder** combines passive and active techniques to improve coverage when hunting for subdomains. It:
- parses `sitemap.xml` (if present),
- scrapes pages with `requests` + `BeautifulSoup`,
- renders JavaScript pages with Selenium to capture dynamic links,
- queries Certificate Transparency (crt.sh) for passive discovery,
- brute-forces subdomains from a wordlist (threaded),
- validates candidates using DNS (dnspython/socket) and HTTP checks,
- prints valid results and optionally writes them to a file using `--output`.

---

## Features

- Static HTML link harvesting with `requests` + `BeautifulSoup`
- JavaScript rendering and harvesting with Selenium + ChromeDriver
- Passive discovery via `crt.sh` (optional)
- Threaded brute-force enumeration (wordlist-driven)
- DNS & HTTP verification (reduces false positives)
- Optional output file (one subdomain per line)
- CLI with helpful arguments for tuning behavior

---

## Requirements

Tested on Python 3.8+

Install required packages:
```bash
python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 selenium webdriver-manager tldextract dnspython
```

You also need Google Chrome (or Chromium) installed if you enable `--selenium`. `webdriver-manager` will attempt to download a matching ChromeDriver automatically.

---

## Usage examples

Basic scan (no brute force, no selenium):
```bash
python subfinder_combined.py example.com
```

With wordlist brute-force (local `subdomains.txt` file):
```bash
python subfinder_combined.py example.com --wordlist subdomains.txt
```

Use Selenium for JS-rendered links and output results to a file:
```bash
python subfinder_combined.py example.com --selenium --wordlist subdomains.txt --output found_subs.txt
```

Use crt.sh passive lookup and verbose output:
```bash
python subfinder_combined.py example.com --crt --verbose --output found_subs.txt
```

---

## CLI arguments (high level)

- `domain` — target root domain (e.g., `example.com`)
- `--wordlist, -w` — path to a newline-separated wordlist for brute-force checks
- `--threads, -t` — number of threads for brute-force (default: 40)
- `--sleep` — optional delay (seconds) between brute requests for throttling
- `--selenium` — enable Selenium (JS rendering)
- `--crt` — query crt.sh for passive subdomain results
- `--max-pages` — limit Selenium scraping to this many pages (default: 10)
- `--verbose` — print failed candidate checks
- `--debug` — run Selenium with visible browser (not headless) for debugging
- `--output, -o` — write validated subdomains to a file (one per line)

---

## How it works (workflow)

1. Parse `sitemap.xml` (if present) to gather seed URLs.  
2. Fetch seed pages with `requests` and extract `<a href>` links using BeautifulSoup.  
3. Optionally render seed pages with Selenium to capture JS-injected links.  
4. Optionally query `crt.sh` for historical certificate entries containing subdomains.  
5. Optionally perform wordlist brute-force to generate candidate subdomains.  
6. Verify each candidate via DNS (A/AAAA) lookup; fallback to HTTP(S) check if DNS fails.  
7. Print validated subdomains and, if `--output` provided, write them to the specified file.

---

## Important implementation notes & tips

- **Selenium vs requests**: Prefer `requests` for static pages (faster). Use Selenium only for pages that generate content via JavaScript.  
- **DNS wildcard detection**: Some domains use wildcard DNS (every subdomain resolves). Consider implementing a simple wildcard check (resolve a random label) to avoid false positives.  
- **Rate limiting & politeness**: Use `--sleep` and lower `--threads` when scanning external domains; aggressive scanning can get you blocked or have legal consequences.  
- **Resilience**: Save intermediate results (harvested links, bruteforce matches) during long runs so you can resume if the script stops.  
- **crt.sh caution**: The public crt.sh JSON endpoint can be rate-limited. Cache results or add retries/backoff if necessary.

---

## Output file format

When `--output found_subs.txt` is used, the file contains one validated subdomain per line, for example:

```
api.example.com
blog.example.com
shop.example.com
```

The file is overwritten if it exists. If you prefer appending instead of overwriting, modify the script to open the file with `"a"` mode.

---

## Example output (console)

```
[+] Starting subdomain discovery for: example.com
[*] Parsing sitemap.xml (if exists)...
  - sitemap URLs found: 3
[*] Querying crt.sh (passive CT lookup)...
  - crt.sh returned: 12 entries
[*] Harvesting with requests + BeautifulSoup (seed pages)...
  - links discovered: 8
[*] Starting Selenium to capture JS-generated links...
  - selenium links discovered: 5
[*] Starting brute-force using wordlist (threads=40)...
  - brute-force found: 4
[*] Verifying candidates (DNS -> HTTP fallback)...
[+] api.example.com (DNS)
[+] blog.example.com (DNS)
[+] shop.example.com (HTTP)

=== Final valid subdomains ===
api.example.com
blog.example.com
shop.example.com

[+] Written 3 subdomains to: found_subs.txt
```

---

## Legal / Ethical

Only run this tool against domains you own or have explicit written permission to test. Unauthorized scanning or enumeration can be illegal and unethical. Respect robots.txt and any program rules for bug bounties or authorized tests.

---

## License

MIT License — free to use for educational and authorized security testing only.

---

**Author:** Preetinder Singh
**Version:** 1.1 

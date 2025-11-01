import argparse
import time
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import tldextract
import dns.resolver
import concurrent.futures
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

HEADERS = {"User-Agent": "subfinder-combined/1.0 (+https://example.com)"}
DEFAULT_TIMEOUT = 5


def get_selenium_driver(headless=True, window_size=(1200, 800)):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")  # newer headless mode
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    # reduce logging
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
    return driver


def fetch_html_with_requests(url,timeout=DEFAULT_TIMEOUT):
    try:
        r=requests.get(url,headers=HEADERS,timeout=timeout,allow_redirects=True)
        return r.status_code,r.text
    except Exception as e:
        return None, None 
    
def fetch_html_with_selenium(url, driver,wait=2):
    try:
        driver.get(url)
        time.sleep(wait) # a wait period for heavy js based sites
        return driver.page_source
    except Exception as e:
        return None,None

def extract_links_from_html(html,base_url):
    soup=BeautifulSoup(html or "" , "html.parser")
    links=set()
    for a in soup.find_all("a",href=True):
        href=a["href"].strip()
        if not href:
            continue
        full=urljoin(base_url,href)
        links.add(full)
    return links

def parse_sitemap(domain):
    urls = set()
    candidates = [
        f"https://{domain}/sitemap.xml",
        f"http://{domain}/sitemap.xml"
    ]
    for sitemap in candidates:
        try:
            r = requests.get(sitemap, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200 and r.text:
                soup = BeautifulSoup(r.text, "xml")
                for loc in soup.find_all("loc"):
                    if loc.text:
                        urls.add(loc.text.strip())
        except Exception:
            pass
    return urls

def subdomain_from_hostname(hostname, root_domain):
    if not hostname:
        return None
    ext = tldextract.extract(hostname)
    domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
    if domain.lower() == root_domain.lower():
        return ext.subdomain if ext.subdomain else None
    return None

def dns_resolves(host):
    try:
        resolver=dns.resolver.Resolver()
        resolver.lifetime(3)
        resolver.timeout(2)
        answers= resolver.resolve(host, "A")
        
        if answers: 
            return True
    except Exception:
        try:
            resolver=dns.resolver.Resolver()
            resolver.lifetime(3)
            resolver.timeout(2)
            answers=resolver.resolve(host, "AAA")
            if answers:
                return True
            
        except Exception:
            return False
        
    return False

def http_check(host, protocol=["https","https"]):
    for p in protocol:
        url=f"{p}://{host}"
        try:
            r= requests.head(url,headers=HEADERS,timeout=4,allow_redirects=True)
            if r.status_code < 400 :
                return True
        except Exception:
            pass
    return False

def harvest_with_requests(domain, start_paths=None):
    start=f"https://{domain}"
    data=set()
    pages={start}
    if start_paths:
        pages.update(start_paths)
    for p in pages:
        status , html=fetch_html_with_requests(p)
        if html:
            links=extract_links_from_html(html, p)
            data.update(links)
    return data
    
def harvest_with_selenium(domain , driver, seed=None, max_page=10 ):
    seeds= seed or [f"http://{domain}" , f"https://{domain}"]
    page_visited=0
    links_found=set()
    for s in seeds:
        if page_visited >= max_page:
            break
        html=fetch_html_with_selenium(driver,s)
        if html:
            link=extract_links_from_html(html)
            links_found.update(link)
            page_visited+=1


    return links_found

def crtsh_lookup(domain):
    """Query crt.sh JSON output for subdomains. (May be rate limited)."""
    out = set()
    try:
        q = f"%25.{domain}"
        url = f"https://crt.sh/?q={q}&output=json"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and r.text:
            # response is a JSON array (may contain duplicates)
            try:
                arr = r.json()
                for item in arr:
                    name = item.get("name_value") or item.get("common_name")
                    if name:
                        # crt.sh often returns newline-separated entries in name_value
                        for candidate in str(name).splitlines():
                            candidate = candidate.strip()
                            if candidate and candidate.endswith(domain):
                                out.add(candidate.lower())
            except Exception:
                pass
    except Exception:
        pass
    return out


def brute_force_check(domain, wordlist_path, threads=30, rate_sleep=0.0):
    found = set()
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        words = [w.strip() for w in f if w.strip() and not w.strip().startswith("#")]

    def check(word):
        host = f"{word}.{domain}"
        # first DNS
        if dns_resolves(host):
            return host
        # then quick HTTP check
        if http_check(host, ("https", "http")):
            return host
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(check, w): w for w in words}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            if res:
                found.add(res)
            if rate_sleep:
                time.sleep(rate_sleep)
    return found


def aggregate_and_filter(found_hosts, root_domain):
    """
    Filter hostnames to only include subdomains of root_domain, and normalized lower-case unique.
    """
    out = set()
    for h in found_hosts:
        try:
            parsed = urlparse(h) if h.startswith("http") else urlparse(f"http://{h}")
            host = parsed.hostname or h
            if not host:
                continue
            if host.lower().endswith(root_domain.lower()):
                out.add(host.lower())
        except Exception:
            pass
    return out
def main(args):
    root_domain = args.domain.strip()
    print(f"[+] Starting subdomain discovery for: {root_domain}")

    # 1) Parse sitemap
    print("[*] Parsing sitemap.xml (if exists)...")
    sitemap_urls = parse_sitemap(root_domain)
    print(f"  - sitemap URLs found: {len(sitemap_urls)}")

    # 2) Passive crt.sh
    if args.crt:
        print("[*] Querying crt.sh (passive CT lookup)...")
        crt_set = crtsh_lookup(root_domain)
        print(f"  - crt.sh returned: {len(crt_set)} entries")
    else:
        crt_set = set()

    # 3) Harvest with requests
    print("[*] Harvesting with requests + BeautifulSoup (seed pages)...")
    req_links = harvest_with_requests(root_domain, start_paths=sitemap_urls if sitemap_urls else None)
    print(f"  - links discovered: {len(req_links)}")

    # 4) Harvest with Selenium (JS-rendered)
    driver = None
    selenium_links = set()
    if args.selenium:
        try:
            print("[*] Starting Selenium to capture JS-generated links (may take time)...")
            driver = get_selenium_driver(headless=not args.debug)
            selenium_links = harvest_with_selenium(root_domain, driver, seeds=list(sitemap_urls)[:5] if sitemap_urls else None, max_pages=args.max_pages)
            print(f"  - selenium links discovered: {len(selenium_links)}")
        except Exception as e:
            print(f"  ! Selenium error: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    # 5) Combine harvested links and extract subdomains
    combined_links = set(req_links) | set(selenium_links) | set(sitemap_urls)
    harvested_subs = set()
    for link in combined_links:
        hostname = urlparse(link).hostname
        sub = subdomain_from_hostname(hostname, root_domain)
        if sub:
            harvested_subs.add(f"{sub}.{root_domain}")

    print(f"[*] Subdomains from link harvesting: {len(harvested_subs)}")

    # 6) Brute-force
    brute_set = set()
    if args.wordlist:
        print("[*] Starting brute-force using wordlist (threads=%d)..." % args.threads)
        brute_set = brute_force_check(root_domain, args.wordlist, threads=args.threads, rate_sleep=args.sleep)
        print(f"  - brute-force found: {len(brute_set)}")

    # 7) Combine everything and verify final resolution (DNS or HTTP)
    all_candidates = set(harvested_subs) | set(brute_set) | set(crt_set)
    print(f"[*] Total unique candidates before verification: {len(all_candidates)}")

    valid = set()
    print("[*] Verifying candidates (DNS -> HTTP fallback)...")
    for host in sorted(all_candidates):
        if dns_resolves(host):
            valid.add(host)
            print(f"[+] {host} (DNS)")
        elif http_check(host, ("https", "http")):
            valid.add(host)
            print(f"[+] {host} (HTTP)")
        else:
            if args.verbose:
                print(f"[-] {host}")

    # Print final results
    print("\n=== Final valid subdomains ===")
    for v in sorted(valid):
        print(v)
    print(f"\n[+] Done. {len(valid)} valid subdomains found.")

    # If user requested output to file, write them
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                for v in sorted(valid):
                    fh.write(v + "\n")
            print(f"[+] Written {len(valid)} subdomains to: {args.output}")
        except Exception as e:
            print(f"[!] Failed to write output file {args.output}: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Combined subdomain finder (Selenium + BS4 + DNS + Brute-force)")
    ap.add_argument("domain", help="Root domain (example.com)")
    ap.add_argument("--wordlist", "-w", help="Path to subdomain wordlist for brute forcing (one word per line)")
    ap.add_argument("--threads", "-t", type=int, default=40, help="Threads for brute forcing")
    ap.add_argument("--sleep", type=float, default=0.0, help="Optional sleep between brute checks per result (throttling)")
    ap.add_argument("--selenium", action="store_true", help="Use Selenium to render JS and harvest links")
    ap.add_argument("--crt", action="store_true", help="Use crt.sh passive lookup")
    ap.add_argument("--max-pages", type=int, default=10, help="Max pages for Selenium harvesting")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    ap.add_argument("--debug", action="store_true", help="Run Selenium non-headless (for debugging)")
    ap.add_argument("--output", "-o", help="Write final validated subdomains to file (one per line)")
    args = ap.parse_args()
    main(args)

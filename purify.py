import re, html, time, sys, os
from curl_cffi import requests as cffi_requests 

URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 35000 
TARGET_DOMAIN = "https://www.iglazura24.pl"

def hard_clean(text):
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    text = html.unescape(text)
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    return "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")

def main():
    scraper = cffi_requests.Session()
    r = scraper.get(URL, impersonate="chrome120", verify=False)
    sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
    all_urls = []
    
    for sub_url in sub_maps:
        sub_url = sub_url.strip().replace("www.iglazura24.pl", "sklep621938.shoparena.pl").replace("www.iglazura24.de", "sklep621938.shoparena.pl")
        if any(x in sub_url.lower() for x in ['products', 'categories']):
            res = scraper.get(sub_url, impersonate="chrome120", verify=False, timeout=90)
            if res.status_code == 200:
                cleaned = hard_clean(res.text)
                blocks = re.findall(r'(?i)<url\b[^>]*>.*?</url>', cleaned, re.DOTALL)
                for b in blocks:
                    if TARGET_DOMAIN in b: 
                        all_urls.append(b)

    for i in range(0, len(all_urls), LIMIT):
        part = (i // LIMIT) + 1
        header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        filename = f"sitemap_part{part}.xml"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header + "\n" + "\n".join(all_urls[i:i + LIMIT]) + "\n</urlset>")
        print(f"Created: {filename}")

if __name__ == "__main__": main()

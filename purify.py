from curl_cffi import requests
import re
import html
import time

# Бьем в технический адрес, чтобы не ловить 403 от Cloudflare
URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def hard_clean(text):
    # 1. Вырезаем мусор Shoper
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    # 2. Превращаем &middot; в точку, &nbsp; в пробел и т.д.
    text = html.unescape(text)
    # 3. XML не ест ничего на букву &, кроме 5 стандартных штук.
    # Поэтому мы сначала все & превращаем в &amp;, а потом исправляем двойное кодирование.
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    # 4. Убираем всё, что может сломать парсер
    return "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")

def main():
    scraper = requests.Session()
    try:
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        
        all_urls = []
        for sub_url in sub_maps:
            sub_url = sub_url.strip().replace("www.iglazura24.pl", "sklep621938.shoparena.pl")
            if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
                res = scraper.get(sub_url, impersonate="chrome120", verify=False, timeout=90)
                if res.status_code == 200:
                    cleaned = hard_clean(res.text)
                    urls = re.findall(r'(?i)<url\b[^>]*>.*?</url>', cleaned, re.DOTALL)
                    all_urls.extend(urls)
        
        # СОХРАНЯЕМ ПОД НОВЫМ ИМЕНЕМ ДЛЯ УБИЙСТВА КЭША
        for i in range(0, len(all_urls), LIMIT):
            chunk = all_urls[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_v3_part{part}.xml"" 
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"Created: {filename}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

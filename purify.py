from curl_cffi import requests
import re
import html
import time

URL = "https://www.iglazura24.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def clean_xml_content(text):
    # 1. Вырезаем мусорные теги Shoper (самое важное)
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    
    # 2. Превращаем HTML-сущности в реальные символы
    text = html.unescape(text)
    
    # 3. ГРУБАЯ СИЛА: Удаляем middot и другие сущности, которые XML не ест
    # XML понимает только 5 сущностей: &amp; &lt; &gt; &quot; &apos;
    # Все остальные (&middot;, &nbsp; и т.д.) ДОЛЖНЫ быть заменены на символы
    replacements = {
        '&middot;': '·',
        '&nbsp;': ' ',
        '&copy;': '©',
        '&reg;': '®',
        '&ndash;': '-',
        '&mdash;': '—'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    # 4. Финальный штрих: экранируем амперсанд (&), если он остался "голым"
    # Но не трогаем уже правильные сущности
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    
    return text

def main():
    print("--- ЗАПУСК ЖЕЛЕЗНОЙ ОЧИСТКИ XML ---")
    scraper = requests.Session()
    r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
    sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
    
    all_urls = []
    for sub_url in sub_maps:
        sub_url = sub_url.strip()
        if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
            print(f"Качаю: {sub_url}")
            res = scraper.get(sub_url, impersonate="chrome120", verify=False, timeout=90)
            if res.status_code == 200:
                cleaned = clean_xml_content(res.text)
                urls = re.findall(r'(?i)<url\b[^>]*>.*?</url>', cleaned, re.DOTALL)
                all_urls.extend(urls)

    for i in range(0, len(all_urls), LIMIT):
        chunk = all_urls[i:i + LIMIT]
        part = (i // LIMIT) + 1
        header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        with open(f"sitemap_part{part}.xml", "w", encoding="utf-8") as f:
            f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
        print(f"Создан файл: sitemap_part{part}.xml")

if __name__ == "__main__":
    main()

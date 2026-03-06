from curl_cffi import requests
import re
import os
import time
import html

URL = "https://www.iglazura24.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def get_with_retry(scraper, url, retries=3):
    """Качает и вычищает XML от всех HTML-ошибок Шоппера"""
    for i in range(retries):
        try:
            res = scraper.get(url, impersonate="chrome120", verify=False, timeout=90)
            if res.status_code == 200:
                # 1. Превращаем &middot; и прочее в реальные символы (·, &, etc)
                content = html.unescape(res.text)
                
                # 2. Вырезаем мусорные теги Shoper
                content = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', content)
                
                # 3. Важнейший шаг: экранируем символ &, который ломает XML
                # Заменяем & на &amp; но только если это не часть тега
                content = content.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                
                # 4. Ищем блоки <url>
                found = re.findall(r'(?i)<url\b[^>]*>.*?</url>', content, re.DOTALL)
                if len(found) > 0:
                    return found
            print(f"  [Попытка {i+1}] Ожидание данных...")
        except Exception as e:
            print(f"  [Попытка {i+1}] Ошибка: {e}")
        time.sleep(3)
    return []

def main():
    print("--- ЗАПУСК ФИНАЛЬНОЙ ОЧИСТКИ (FIX XML ERRORS) ---")
    scraper = requests.Session()
    
    try:
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено под-карт: {len(sub_maps)}")

        all_urls = []
        for index, sub_url in enumerate(sub_maps):
            sub_url = sub_url.strip()
            if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"[{index+1}/{len(sub_maps)}] Качаю и лечу XML: {sub_url}")
                urls = get_with_retry(scraper, sub_url)
                all_urls.extend(urls)
                print(f"  + собрано: {len(urls)} чистых ссылок")

        print(f"\n--- ИТОГО: {len(all_urls)} ссылок без ошибок ---")

        for i in range(0, len(all_urls), LIMIT):
            chunk = all_urls[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_part{part}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"ФАЙЛ ОБНОВЛЕН: {filename}")

    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()

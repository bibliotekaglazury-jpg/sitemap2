from curl_cffi import requests
import re
import os

# Основной адрес (теперь мы можем бить прямо в него!)
URL = "https://www.iglazura24.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def main():
    print("--- ЗАПУСК: МАСКИРОВКА ПОД CHROME (TLS IMPERSONATION) ---")
    
    try:
        # impersonate="chrome120" делает наш запрос ИДЕНТИЧНЫМ реальному браузеру
        # verify=False здесь сработает корректно
        print(f"Запрашиваю индекс: {URL}")
        r = requests.get(URL, impersonate="chrome120", verify=False, timeout=60)
        
        print(f"Статус ответа: {r.status_code}")
        
        if r.status_code != 200:
            print(f"Блокировка не снята. Ответ: {r.text[:200]}")
            return

        # Ищем под-карты
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено под-карт: {len(sub_maps)}")

        all_urls = []
        for sub_url in sub_maps:
            sub_url = sub_url.strip()
            if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"Качаю: {sub_url}")
                res = requests.get(sub_url, impersonate="chrome120", verify=False, timeout=60)
                
                # Чистим мусор Shoper
                content = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', res.text)
                urls = re.findall(r'(?i)<url>.*?</url>', content, re.DOTALL)
                all_urls.extend(urls)
                print(f"  + {len(urls)} ссылок")

        if all_urls:
            print(f"--- ИТОГО СОБРАНО: {len(all_urls)} ---")
            for i in range(0, len(all_urls), LIMIT):
                chunk = all_urls[i:i + LIMIT]
                part = (i // LIMIT) + 1
                header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                filename = f"sitemap_part{part}.xml"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
                print(f"СОЗДАН: {filename}")
        else:
            print("Список пуст.")

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")

if __name__ == "__main__":
    main()

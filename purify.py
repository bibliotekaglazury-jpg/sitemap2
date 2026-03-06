from curl_cffi import requests
import re
import html
import time

# ИСПОЛЬЗУЕМ ТЕХНИЧЕСКИЙ АДРЕС, ЧТОБЫ МЕНЬШЕ БЕСИТЬ ШОППЕР
URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def clean_xml(text):
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    text = html.unescape(html.unescape(text))
    text = text.replace('&middot;', '·').replace('&nbsp;', ' ')
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")
    return text

def main():
    print("--- ЗАПУСК СТЕРИЛИЗАЦИИ XML V2 ---")
    scraper = requests.Session()
    
    try:
        print(f"Запрашиваю индекс: {URL}")
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        print(f"Статус индекса: {r.status_code}")
        
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено под-карт: {len(sub_maps)}")

        if not sub_maps:
            print("ОШИБКА: Список под-карт пуст. Шоппер выдал пустую страницу.")
            print(f"Начало ответа: {r.text[:500]}")
            return

        all_urls = []
        for index, sub_url in enumerate(sub_maps):
            sub_url = sub_url.strip()
            if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"[{index+1}/{len(sub_maps)}] Качаю: {sub_url}")
                res = scraper.get(sub_url, impersonate="chrome120", verify=False, timeout=90)
                if res.status_code == 200:
                    cleaned = clean_xml(res.text)
                    urls = re.findall(r'(?i)<url\b[^>]*>.*?</url>', cleaned, re.DOTALL)
                    all_urls.extend(urls)
                    print(f"  + {len(urls)} ссылок")
                time.sleep(1) # Небольшая пауза, чтобы не злить сервер

        print(f"\nИТОГО СОБРАНО: {len(all_urls)}")

        if all_urls:
            for i in range(0, len(all_urls), LIMIT):
                chunk = all_urls[i:i + LIMIT]
                part = (i // LIMIT) + 1
                header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                # МЕНЯЕМ ИМЯ ФАЙЛА ДЛЯ УБИЙСТВА КЭША
                filename = f"sitemap_new_part{part}.xml"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
                print(f"СОЗДАН НОВЫЙ ФАЙЛ: {filename}")
        else:
            print("ОШИБКА: Ссылки не собраны.")

    except Exception as e:
        print(f"КРИТИЧЕСКИЙ СБОЙ: {e}")

if __name__ == "__main__":
    main()

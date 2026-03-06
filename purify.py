import cloudscraper
import re
import os
import urllib3

# Отключаем предупреждения о небезопасном соединении (чтобы не спамить в логи)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Твои адреса (пробуем по очереди)
URLS_TO_TRY = [
    "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap",
    "http://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
]
LIMIT = 45000

def main():
    print(f"--- ЗАПУСК: ОБХОД SSL И CLOUDFLARE ---")
    
    # Создаем скрапер, который игнорирует ошибки SSL (verify=False)
    scraper = cloudscraper.create_scraper()
    
    content_index = ""
    for url in URLS_TO_TRY:
        try:
            print(f"Попытка соединения с: {url}")
            # verify=False — это ключ к успеху, игнорируем старые протоколы Shoper
            r = scraper.get(url, timeout=60, verify=False)
            
            if r.status_code == 200 and "<loc>" in r.text.lower():
                content_index = r.text
                print("УСПЕХ! Данные получены.")
                break
            else:
                print(f"Статус: {r.status_code}. XML не найден.")
        except Exception as e:
            print(f"Ошибка на этом адресе: {e}")

    if not content_index:
        print("КРИТИЧЕСКАЯ ОШИБКА: Не удалось достучаться до Shoper даже без SSL.")
        return

    # Парсим под-карты
    sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', content_index)
    all_urls = []

    for sub_url in sub_maps:
        sub_url = sub_url.strip()
        if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
            print(f"Качаем: {sub_url}")
            try:
                # Везде добавляем verify=False
                res = scraper.get(sub_url, timeout=60, verify=False)
                
                # Если под-карта на основном домене не открывается, пробуем тех-адрес
                if res.status_code != 200:
                    tech_sub = sub_url.replace("www.iglazura24.pl", "sklep621938.shoparena.pl")
                    res = scraper.get(tech_sub, timeout=60, verify=False)

                content = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', res.text)
                urls = re.findall(r'(?i)<url>.*?</url>', content, re.DOTALL)
                all_urls.extend(urls)
                print(f"  + получено: {len(urls)}")
            except:
                print(f"  ! ошибка загрузки {sub_url}")

    if all_urls:
        for i in range(0, len(all_urls), LIMIT):
            chunk = all_urls[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_part{part}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"ГОТОВО: {filename}")
    else:
        print("Список ссылок пуст.")

if __name__ == "__main__":
    main()

import cloudscraper
import re
import os

# Твоя техническая ссылка (прямой доступ к базе без Cloudflare)
TECH_URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def main():
    print(f"--- ЗАПУСК ЧЕРЕЗ ТЕХНИЧЕСКИЙ КАНАЛ ---")
    
    # Используем cloudscraper на случай, если даже там есть базовая защита
    scraper = cloudscraper.create_scraper()
    
    try:
        print(f"Запрашиваю: {TECH_URL}")
        r = scraper.get(TECH_URL, timeout=60)
        
        print(f"Статус ответа: {r.status_code}")
        
        if r.status_code != 200:
            print(f"Ошибка! Сервер ответил: {r.status_code}")
            return

        # Ищем все под-карты <loc>
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено под-карт в индексе: {len(sub_maps)}")

        all_urls = []
        for url in sub_maps:
            url = url.strip()
            # Берем только товары и категории
            if any(x in url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"Качаю данные из: {url}")
                # Если под-карта ведет на основной домен, пробуем достучаться
                res = scraper.get(url, timeout=60)
                
                # Если основной домен блокирует под-карты, меняем его на технический на лету
                if res.status_code != 200:
                    tech_sub_url = url.replace("www.iglazura24.pl", "sklep621938.shoparena.pl")
                    print(f"  Доступ к основному закрыт, пробую тех-адрес: {tech_sub_url}")
                    res = scraper.get(tech_sub_url, timeout=60)

                # Вырезаем лишние теги Shoper (name, parentid, productscount)
                content = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', res.text)
                
                # Вытаскиваем все блоки <url>...</url>
                urls = re.findall(r'(?i)<url>.*?</url>', content, re.DOTALL)
                all_urls.extend(urls)
                print(f"  + получено ссылок: {len(urls)}")

        print(f"--- ИТОГО СОБРАНО: {len(all_urls)} ---")

        if not all_urls:
            print("Список пуст. Файлы не созданы.")
            return

        # Разбиваем на файлы по 45 000 ссылок
        for i in range(0, len(all_urls), LIMIT):
            chunk = all_urls[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_part{part}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"УСПЕХ: Создан файл {filename}")

    except Exception as e:
        print(f"ОШИБКА: {e}")

if __name__ == "__main__":
    main()

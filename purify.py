import requests
import re
import os

# Продвинутые заголовки, чтобы Shoper думал, что мы — Макбук Шефа
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

INDEX_URL = "https://www.iglazura24.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def main():
    print("--- ЗАПУСК ДИАГНОСТИКИ ---")
    try:
        print(f"Стучимся по адресу: {INDEX_URL}")
        r = requests.get(INDEX_URL, headers=HEADERS, timeout=30)
        
        print(f"Статус ответа: {r.status_code}")
        
        # Если пусто или ошибка — печатаем ЧТО ТАМ
        if not r.text.strip():
            print("ОШИБКА: Сервер вернул абсолютно пустой ответ!")
            return
            
        if "<loc>" not in r.text.lower():
            print("ОШИБКА: В ответе нет тегов <loc>. Вот первые 500 символов того, что прислал Shoper:")
            print("-" * 50)
            print(r.text[:500])
            print("-" * 50)
            return

        # Если дошли сюда, значит XML живой
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено ссылок в индексе: {len(sub_maps)}")

        all_urls = []
        for url in sub_maps:
            url = url.strip()
            if any(x in url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"Обработка: {url}")
                res = requests.get(url, headers=HEADERS, timeout=30)
                content = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', res.text)
                urls = re.findall(r'(?i)<url>.*?</url>', content, re.DOTALL)
                all_urls.extend(urls)
                print(f"  + добавлено {len(urls)} ссылок")

        if all_urls:
            for i in range(0, len(all_urls), LIMIT):
                chunk = all_urls[i:i + LIMIT]
                part = (i // LIMIT) + 1
                header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                with open(f"sitemap_part{part}.xml", "w", encoding="utf-8") as f:
                    f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
                print(f"Файл создан: sitemap_part{part}.xml")
        else:
            print("ИТОГ: Ссылок не набралось. Проверь фильтры (products/categories).")

    except Exception as e:
        print(f"ВЗРЫВ СКРИПТА: {e}")

if __name__ == "__main__":
    main()

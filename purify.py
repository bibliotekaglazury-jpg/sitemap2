from curl_cffi import requests
import re
import html
import time

# Используем основной домен, так как curl_cffi его пробивает
URL = "https://www.iglazura24.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def clean_block(block):
    # 1. Удаляем запрещенные теги Shoper (name, parentid и т.д.)
    block = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', block)
    
    # 2. Лечим middot и другие HTML-сущности
    # Сначала превращаем &middot; в реальный символ ·
    block = html.unescape(block)
    
    # 3. XML-безопасность: заменяем & на &amp; (но только если это не часть другого тега)
    # Это предотвращает поломку XML амперсандами в URL
    block = block.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    
    # 4. Удаляем любые невидимые символы, которые бесят парсеры
    block = "".join(ch for ch in block if ord(ch) >= 32 or ch in "\n\r\t")
    return block

def main():
    print("--- ЗАПУСК ХИРУРГИЧЕСКОЙ ОЧИСТКИ XML ---")
    scraper = requests.Session()
    
    try:
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено под-карт: {len(sub_maps)}")

        all_urls = []
        for index, sub_url in enumerate(sub_maps):
            sub_url = sub_url.strip()
            if any(x in sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"[{index+1}/{len(sub_maps)}] Обработка: {sub_url}")
                res = scraper.get(sub_url, impersonate="chrome120", verify=False, timeout=90)
                
                if res.status_code == 200:
                    # Ищем все блоки <url>...</url>
                    raw_urls = re.findall(r'(?i)<url>.*?</url>', res.text, re.DOTALL)
                    for block in raw_urls:
                        all_urls.append(clean_block(block))
                    print(f"  + успешно извлечено: {len(raw_urls)} ссылок")
                time.sleep(0.5)

        print(f"\n--- ИТОГО СОБРАНО: {len(all_urls)} ссылок ---")

        if not all_urls:
            print("ОШИБКА: Ссылки не найдены! Проверь ответ сервера.")
            return

        # Сохраняем в файлы с НОВЫМ ИМЕНЕМ для обхода кэша
        for i in range(0, len(all_urls), LIMIT):
            chunk = all_urls[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_new_part{part}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"СОЗДАН ФАЙЛ: {filename}")

    except Exception as e:
        print(f"КРИТИЧЕСКИЙ СБОЙ: {e}")

if __name__ == "__main__":
    main()

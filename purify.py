from curl_cffi import requests
import re
import html
import time

# БЬЕМ ТОЛЬКО В ТЕХНИЧЕСКИЙ АДРЕС (БЕЗ CLOUDFLARE)
URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

def clean_block(block):
    # Вырезаем мусор Shoper
    block = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', block)
    # Лечим спецсимволы (middot и прочее)
    block = html.unescape(block)
    block = block.replace('&middot;', '·').replace('&nbsp;', ' ')
    # Важно для XML: экранируем амперсанд
    block = block.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    # Убираем мусорные символы
    return "".join(ch for ch in block if ord(ch) >= 32 or ch in "\n\r\t")

def main():
    print("--- ЗАПУСК ЧЕРЕЗ ТЕХНИЧЕСКИЙ КАНАЛ (БЕЗ БЛОКИРОВОК) ---")
    scraper = requests.Session()
    
    try:
        print(f"Стучимся в служебный вход: {URL}")
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        print(f"Статус ответа: {r.status_code}")
        
        if r.status_code != 200:
            print(f"Ошибка! Сервер Shoper ответил: {r.status_code}")
            return

        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"Найдено под-карт: {len(sub_maps)}")

        all_urls = []
        for index, sub_url in enumerate(sub_maps):
            sub_url = sub_url.strip()
            # Важно: если ссылка внутри ведет на основной домен, меняем её на технический
            tech_sub_url = sub_url.replace("www.iglazura24.pl", "sklep621938.shoparena.pl")
            
            if any(x in tech_sub_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"[{index+1}/{len(sub_maps)}] Качаю: {tech_sub_url}")
                try:
                    res = scraper.get(tech_sub_url, impersonate="chrome120", verify=False, timeout=90)
                    if res.status_code == 200:
                        raw_urls = re.findall(r'(?i)<url>.*?</url>', res.text, re.DOTALL)
                        for block in raw_urls:
                            all_urls.append(clean_block(block))
                        print(f"  + получено: {len(raw_urls)} ссылок")
                    else:
                        print(f"  ! ошибка {res.status_code}")
                except Exception as e:
                    print(f"  ! сбой связи: {e}")
                time.sleep(0.3)

        print(f"\n--- ИТОГО СОБРАНО: {len(all_urls)} ссылок ---")

        if all_urls:
            for i in range(0, len(all_urls), LIMIT):
                chunk = all_urls[i:i + LIMIT]
                part = (i // LIMIT) + 1
                header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                filename = f"sitemap_new_part{part}.xml"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
                print(f"ФАЙЛ СОЗДАН: {filename}")
        else:
            print("Ошибка: Ссылки не найдены.")

    except Exception as e:
        print(f"КРИТИЧЕСКИЙ СБОЙ: {e}")

if __name__ == "__main__":
    main()

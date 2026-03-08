from curl_cffi import requests
import re
import html
import time
import sys

# Используем технический адрес для получения данных без Cloudflare
URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000
TARGET_DOMAIN_KEYWORD = "iglazura24.pl" # !!! Ключевое слово для фильтрации !!!
TARGET_SHOPARENA_KEYWORD = "sklep621938.shoparena.pl"


def hard_clean(text):
    # 1. Вырезаем мусор Shoper
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    # 2. Декодируем HTML сущности
    text = html.unescape(text)
    # 3. Фикс для амперсанда (единственный разрешенный символ на &)
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    # 4. Очистка от невидимых символов
    return "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")

def main():
    scraper = requests.Session()
    print(f"🚀 Запуск очистки XML для {TARGET_DOMAIN_KEYWORD} через {URL}")
    try:
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        if r.status_code != 200:
            print(f"⛔ Ошибка при доступе к индексу Shoper: {r.status_code}")
            sys.exit(1) # Выходим с ошибкой

        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"📂 Найдено под-карт в индексе Shoper: {len(sub_maps)}")
        
        all_urls_for_sitemap = [] # Здесь будут только нужные URL
        
        for sub_url in sub_maps:
            sub_url = sub_url.strip()
            # Меняем основной домен на технический для скачивания
            fetch_url = sub_url.replace(TARGET_DOMAIN_KEYWORD, TARGET_SHOPARENA_KEYWORD)

            # Проверяем, что это ссылка на продукт/категорию/новости/инфо
            if any(x in fetch_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"  🔍 Обработка под-карты: {sub_url.split('/')[-1]}", end=" ", flush=True)
                
                res = scraper.get(fetch_url, impersonate="chrome120", verify=False, timeout=90)
                if res.status_code == 200:
                    cleaned_content = hard_clean(res.text)
                    raw_urls_blocks = re.findall(r'(?i)<url>.*?</url>', cleaned_content, re.DOTALL)
                    
                    filtered_count = 0
                    for url_block in raw_urls_blocks:
                        # Извлекаем loc из блока URL, чтобы проверить домен
                        loc_match = re.search(r'<loc>(.*?)</loc>', url_block)
                        if loc_match:
                            original_loc_url = loc_match.group(1)
                            # !!! КЛЮЧЕВАЯ ФИЛЬТРАЦИЯ !!!
                            if TARGET_DOMAIN_KEYWORD in original_loc_url:
                                all_urls_for_sitemap.append(url_block)
                                filtered_count += 1
                    print(f"✅ Добавлено: {filtered_count} ссылок")
                else:
                    print(f"⛔ Сбой при загрузке под-карты: {res.status_code} для {fetch_url}")
            time.sleep(0.5) # Небольшая пауза

        print(f"\n📊 ИТОГО СОБРАНО и ОТФИЛЬТРОВАНО для {TARGET_DOMAIN_KEYWORD}: {len(all_urls_for_sitemap)} ссылок.")

        if not all_urls_for_sitemap:
            print("⚠️ ВНИМАНИЕ: После фильтрации не осталось ссылок. Возможно, неверный TARGET_DOMAIN_KEYWORD.")
            sys.exit(1)

        # СОХРАНЯЕМ В НОВЫЕ ФАЙЛЫ V5
        for i in range(0, len(all_urls_for_sitemap), LIMIT):
            chunk = all_urls_for_sitemap[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_v5_part{part}.xml" 
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"💾 СОЗДАН ФАЙЛ: {filename} с {len(chunk)} ссылками.")

    except Exception as e:
        print(f"💥 КРИТИЧЕСКИЙ СБОЙ СКРИПТА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

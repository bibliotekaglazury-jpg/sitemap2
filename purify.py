import requests
import re
import html
import time
import sys
import os # Добавили os для создания каталогов

# Используем технический адрес для получения данных без Cloudflare
URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000

# !!! КЛЮЧЕВЫЕ НАСТРОЙКИ ДЛЯ НОВОЙ СТРУКТУРЫ И ФИЛЬТРАЦИИ !!!
CLIENT_SLUG = "iglazura24" # Уникальный идентификатор клиента (для SaaS)
SITEMAP_VERSION = "v6"     # Текущая версия

TARGET_DOMAIN_FILTER = f"https://www.{CLIENT_SLUG}.pl" # Домен для строгой фильтрации
SHOPARENA_TECHNICAL_DOMAIN = "sklep621938.shoparena.pl" # Технический домен Shoper

# Путь, куда будут сохраняться файлы на GitHub Actions
OUTPUT_DIR = f"client_sitemaps/{CLIENT_SLUG}/{SITEMAP_VERSION}"


def hard_clean(text):
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    text = html.unescape(text)
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    return "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")

def main():
    scraper = requests.Session()
    print(f"🚀 Запуск очистки XML для '{TARGET_DOMAIN_FILTER}' через '{URL}'")
    try:
        r = scraper.get(URL, impersonate="chrome120", verify=False, timeout=60)
        if r.status_code != 200:
            print(f"⛔ Ошибка при доступе к индексу Shoper: {r.status_code}")
            sys.exit(1)

        sub_maps = re.findall(r'(?i)<loc>(.*?)</loc>', r.text)
        print(f"📂 Найдено под-карт в индексе Shoper: {len(sub_maps)}")
        
        all_urls_for_sitemap = [] 
        initial_urls_count = 0
        
        for sub_url in sub_maps:
            sub_url = sub_url.strip()
            
            fetch_url = sub_url.replace(f"https://www.{CLIENT_SLUG}.pl", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            fetch_url = fetch_url.replace(f"https://www.{CLIENT_SLUG}.de", f"https://{SHOPARENA_TECHNICAL_DOMAIN}") # Заменяем DE на тех. домен
            fetch_url = fetch_url.replace(f"http://www.{CLIENT_SLUG}.pl", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            fetch_url = fetch_url.replace(f"http://www.{CLIENT_SLUG}.de", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            

            if any(x in fetch_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"  🔍 Обработка под-карты: {sub_url.split('/')[-1]}", end=" ", flush=True)
                
                res = scraper.get(fetch_url, impersonate="chrome120", verify=False, timeout=90)
                if res.status_code == 200:
                    cleaned_content = hard_clean(res.text)
                    raw_urls_blocks = re.findall(r'(?i)<url>.*?</url>', cleaned_content, re.DOTALL)
                    
                    initial_urls_count += len(raw_urls_blocks)
                    filtered_out_count = 0

                    for url_block in raw_urls_blocks:
                        loc_match = re.search(r'<loc>(.*?)</loc>', url_block)
                        if loc_match:
                            original_loc_url = loc_match.group(1)
                            if original_loc_url.startswith(TARGET_DOMAIN_FILTER):
                                all_urls_for_sitemap.append(url_block)
                            else:
                                filtered_out_count += 1
                        else:
                            if not url_block.startswith(TARGET_DOMAIN_FILTER):
                                filtered_out_count += 1
                    
                    print(f"✅ Добавлено: {len(all_urls_for_sitemap) - (initial_urls_count - len(raw_urls_blocks))} ссылок (отфильтровано в этой под-карте: {filtered_out_count})")
                else:
                    print(f"⛔ Сбой при загрузке под-карты: {res.status_code} для {fetch_url}")
            time.sleep(0.5)

        print(f"\n📊 ИТОГО ДО ФИЛЬТРАЦИИ: {initial_urls_count} ссылок.")
        print(f"📊 ИТОГО ОТФИЛЬТРОВАНО (не '{TARGET_DOMAIN_FILTER}'): {initial_urls_count - len(all_urls_for_sitemap)} ссылок.")
        print(f"📊 ИТОГО СОБРАНО для '{TARGET_DOMAIN_FILTER}': {len(all_urls_for_sitemap)} ссылок.")

        if not all_urls_for_sitemap:
            print("⚠️ ВНИМАНИЕ: После фильтрации не осталось ссылок. Проверьте TARGET_DOMAIN_FILTER.")
            sys.exit(1)

        # --- Создаем директории, если их нет ---
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # СОХРАНЯЕМ В НОВЫЕ ФАЙЛЫ V6 В НОВОЙ СТРУКТУРЕ
        for i in range(0, len(all_urls_for_sitemap), LIMIT):
            chunk = all_urls_for_sitemap[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = os.path.join(OUTPUT_DIR, f"sitemap_part{part}.xml") # Новый путь и имя файла
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"💾 СОЗДАН ФАЙЛ: {filename} с {len(chunk)} ссылками.")

    except Exception as e:
        print(f"💥 КРИТИЧЕСКИЙ СБОЙ СКРИПТА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

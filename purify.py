from curl_cffi import requests
import re
import html
import time
import sys

# Используем технический адрес для получения данных без Cloudflare
URL = "https://sklep621938.shoparena.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000
# !!! КЛЮЧЕВОЕ СТРОГОЕ СЛОВО ДЛЯ ФИЛЬТРАЦИИ !!!
# Будут пропускаться только URL, которые НАЧИНАЮТСЯ с этого домена
TARGET_DOMAIN_FILTER = "https://www.iglazura24.pl" 
# Заменяем основной домен на технический для запросов к Shoper
SHOPARENA_TECHNICAL_DOMAIN = "sklep621938.shoparena.pl" 


def hard_clean(text):
    # 1. Вырезаем мусор Shoper (name, parentid, productscount)
    text = re.sub(r'(?i)<(name|parentid|productscount)>.*?</\1>', '', text)
    # 2. Декодируем HTML сущности (превращаем &middot; в ·, &nbsp; в пробел)
    text = html.unescape(text)
    # 3. Фикс для амперсанда (единственный разрешенный символ на &)
    # Сначала все & превращаем в &amp;, затем исправляем двойное кодирование
    text = text.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    # 4. Очистка от невидимых символов
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
        
        all_urls_for_sitemap = [] # Здесь будут только отфильтрованные URL
        initial_urls_count = 0
        
        for sub_url in sub_maps:
            sub_url = sub_url.strip()
            
            # --- Важный шаг: Заменяем ДОМЕНЫ в URL на технический для скачивания ---
            # Это гарантирует, что мы всегда стучимся в shoparena.pl, даже если loc-ссылка от Shoper на www.iglazura24.de
            fetch_url = sub_url.replace("https://www.iglazura24.pl", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            fetch_url = fetch_url.replace("https://www.iglazura24.de", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            fetch_url = fetch_url.replace("http://www.iglazura24.pl", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            fetch_url = fetch_url.replace("http://www.iglazura24.de", f"https://{SHOPARENA_TECHNICAL_DOMAIN}")
            

            if any(x in fetch_url.lower() for x in ['products', 'categories', 'news', 'info']):
                print(f"  🔍 Обработка под-карты: {sub_url.split('/')[-1]}", end=" ", flush=True)
                
                res = scraper.get(fetch_url, impersonate="chrome120", verify=False, timeout=90)
                if res.status_code == 200:
                    cleaned_content = hard_clean(res.text)
                    raw_urls_blocks = re.findall(r'(?i)<url>.*?</url>', cleaned_content, re.DOTALL)
                    
                    initial_urls_count += len(raw_urls_blocks) # Считаем все URL до фильтрации
                    filtered_out_count = 0

                    for url_block in raw_urls_blocks:
                        loc_match = re.search(r'<loc>(.*?)</loc>', url_block)
                        if loc_match:
                            original_loc_url = loc_match.group(1)
                            # !!! КЛЮЧЕВАЯ СТРОГАЯ ФИЛЬТРАЦИЯ: пропускаем только URL польского домена !!!
                            if original_loc_url.startswith(TARGET_DOMAIN_FILTER): # Используем startswith для строгой проверки
                                all_urls_for_sitemap.append(url_block)
                            else:
                                filtered_out_count += 1
                        else:
                            # Если loc-тег не найден, и блок не начинается с целевого домена, фильтруем
                            if not url_block.startswith(TARGET_DOMAIN_FILTER):
                                filtered_out_count += 1
                    
                    print(f"✅ Добавлено: {len(all_urls_for_sitemap) - (initial_urls_count - len(raw_urls_blocks))} ссылок (отфильтровано в этой под-карте: {filtered_out_count})")
                else:
                    print(f"⛔ Сбой при загрузке под-карты: {res.status_code} для {fetch_url}")
            time.sleep(0.5) # Небольшая пауза

        print(f"\n📊 ИТОГО ДО ФИЛЬТРАЦИИ: {initial_urls_count} ссылок.")
        print(f"📊 ИТОГО ОТФИЛЬТРОВАНО (не '{TARGET_DOMAIN_FILTER}'): {initial_urls_count - len(all_urls_for_sitemap)} ссылок.")
        print(f"📊 ИТОГО СОБРАНО для '{TARGET_DOMAIN_FILTER}': {len(all_urls_for_sitemap)} ссылок.")

        if not all_urls_for_sitemap:
            print("⚠️ ВНИМАНИЕ: После фильтрации не осталось ссылок. Проверьте TARGET_DOMAIN_FILTER.")
            sys.exit(1) # Выходим с ошибкой, если ссылок нет

        # СОХРАНЯЕМ В НОВЫЕ ФАЙЛЫ V6
        for i in range(0, len(all_urls_for_sitemap), LIMIT):
            chunk = all_urls_for_sitemap[i:i + LIMIT]
            part = (i // LIMIT) + 1
            header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            filename = f"sitemap_v6_part{part}.xml" 
            with open(filename, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(chunk) + "\n</urlset>")
            print(f"💾 СОЗДАН ФАЙЛ: {filename} с {len(chunk)} ссылками.")

    except Exception as e:
        print(f"💥 КРИТИЧЕСКИЙ СБОЙ СКРИПТА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

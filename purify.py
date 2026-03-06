import requests
import re

INDEX_URL = "https://www.iglazura24.pl/console/integration/execute/name/GoogleSitemap"
LIMIT = 45000 

def main():
    print("Start cleaning...")
    r = requests.get(INDEX_URL)
    sub_maps = re.findall(r'<loc>(.*?)</loc>', r.text)
    
    all_urls = []
    for url in sub_maps:
        if any(x in url for x in ['products', 'categories', 'news', 'info']):
            print(f"Processing: {url}")
            content = requests.get(url).text
            # Вырезаем мусорные теги Shoper
            content = re.sub(r'<(name|parentid|productscount)>.*?</\1>', '', content)
            urls = re.findall(r'<url>.*?</url>', content, re.DOTALL)
            all_urls.extend(urls)

    # Сохраняем части по 45к ссылок
    for i in range(0, len(all_urls), LIMIT):
        chunk = all_urls[i:i + LIMIT]
        part = (i // LIMIT) + 1
        header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        with open(f"sitemap_part{part}.xml", "w", encoding="utf-8") as f:
            f.write(header + "\n".join(chunk) + "</urlset>")
    print("Done!")

if __name__ == "__main__":
    main()

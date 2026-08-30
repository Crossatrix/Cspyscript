import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import time
import random

# Konfiguration
TARGET_API_URL = "https://crossisearch.lovable.app/api/public/submit"
API_KEY = "csk_adm_e5133d11c5d7aa8f2f29c13758dab6a6f95605f9688c386c50b7e04791bfc5fd"
TOTAL_ARTICLES = 300
MAX_WORKERS = 20

def fetch_random_wikipedia_urls(limit):
    urls = []
    headers = {"User-Agent": "MobileMultiLangFetcher/1.3 (Python-urllib)"}
    languages = ["en", "de", "ja", "ru", "fr", "es", "zh", "it", "pl", "pt"]
    
    while len(urls) < limit:
        needed = min(50, limit - len(urls))
        lang = random.choice(languages)
        api_url = f"https://{lang}.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "format": "json",
            "list": "random",
            "rnnamespace": 0,
            "rnlimit": needed
        }
        url_params = urllib.parse.urlencode(params)
        full_url = f"{api_url}?{url_params}"
        
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    random_pages = data.get("query", {}).get("random", [])
                    for page in random_pages:
                        safe_title = page["title"].replace(" ", "_")
                        safe_title_encoded = urllib.parse.quote(safe_title)
                        url = f"https://{lang}.wikipedia.org/wiki/{safe_title_encoded}"
                        # Speichere die Sprache als Metadaten mit dem Link ab
                        urls.append({"url": url, "lang": lang})
                    print(f"-> {len(urls)} von {limit} Artikeln geladen (Letzter Block: {lang.upper()})...")
                else:
                    print(f"Wikipedia Fehler ({lang}): Status {response.status}. Wiederhole...")
                    time.sleep(1)
        except Exception as e:
            print(f"Verbindungsfehler bei Wikipedia ({lang}): {e}. Wiederhole...")
            time.sleep(1)
            
    random.shuffle(urls)
    return urls

def send_to_target_api(article_data, index):
    url = article_data["url"]
    lang = article_data["lang"]
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Mobile)"
    }
    payload = json.dumps({"kind": "page", "url": url}).encode("utf-8")
    req = urllib.request.Request(TARGET_API_URL, data=payload, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status in (200, 201):
                print(f"[{index}/{TOTAL_ARTICLES}] [{lang.upper()}] Gesendet: {url}")
                return lang, True
            else:
                print(f"[{index}/{TOTAL_ARTICLES}] [{lang.upper()}] API-Status {response.status} bei: {url}")
                return lang, False
    except Exception as e:
        print(f"[{index}/{TOTAL_ARTICLES}] [{lang.upper()}] Fehler bei {url}: {e}")
        return lang, False

def main():
    print(f"Generiere {TOTAL_ARTICLES} Wikipedia-Links aus 10 Sprachen...")
    wiki_articles = fetch_random_wikipedia_urls(TOTAL_ARTICLES)
    print(f"\nLinks bereit. Starte High-Speed Übertragung...\n")
    
    # Statistik-Dictionaries vorbereiten
    stats = {}
    
    # Sende Daten über den ThreadPool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_to_target_api, article, index) for index, article in enumerate(wiki_articles, start=1)]
        
        for future in futures:
            lang, success = future.result()
            
            # Initialisiere Zähler für die Sprache, falls noch nicht vorhanden
            if lang not in stats:
                stats[lang] = {"total": 0, "success": 0}
                
            stats[lang]["total"] += 1
            if success:
                stats[lang]["success"] += 1
                
    # Abschlussübersicht ausgeben
    print("\n" + "="*40)
    print("           ABSCHLUSSÜBERSICHT          ")
    print("="*40)
    print(f"{'Sprache':<10} | {'Erfolgreich':<12} / {'Gesamt':<8} | {'Erfolgsquote'}")
    print("-"*40)
    
    total_success = 0
    # Sortiert nach Sprache (DE, EN, ES...)
    for lang in sorted(stats.keys()):
        s_count = stats[lang]["success"]
        t_count = stats[lang]["total"]
        total_success += s_count
        percentage = (s_count / t_count * 100) if t_count > 0 else 0
        print(f"{lang.upper():<10} | {s_count:<12} / {t_count:<8} | {percentage:.1f}%")
        
    print("-"*40)
    print(f"{'GESAMT':<10} | {total_success:<12} / {TOTAL_ARTICLES:<8} | {(total_success/TOTAL_ARTICLES*100):.1f}%")
    print("="*40)

if __name__ == "__main__":
    main()

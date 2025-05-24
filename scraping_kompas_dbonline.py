import requests
from bs4 import BeautifulSoup
import time
import re
from pymongo import MongoClient

def scrape_kompas_crime():
    base_url = "https://www.kompas.com/tag/pencurian-minimarket"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    all_data = []
    page = 1

    while True:
        print(f"Mengambil halaman {page}...")
        url = f"{base_url}?page={page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Gagal mengambil halaman {page}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # Deteksi halaman kosong
        if soup.find("div", class_="searchContent --emptyAlart"):
            print("Halaman kosong ditemukan, selesai scraping.")
            break

        article_list = soup.find("div", class_="articleList -list")
        if not article_list:
            print("Tidak menemukan daftar artikel di halaman ini.")
            break

        articles = article_list.find_all("div", class_="articleItem")
        if not articles:
            print("Artikel kosong di halaman ini.")
            break

        for article in articles:
            try:
                link_tag = article.find("a", class_="article-link")
                if not link_tag:
                    continue

                link = link_tag["href"]
                title_tag = article.find("h2", class_="articleTitle")
                title = title_tag.get_text(strip=True) if title_tag else "Tidak ada judul"

                date_tag = article.find("div", class_="articlePost-date")
                date = date_tag.get_text(strip=True) if date_tag else "Tidak ada tanggal"

                waktu_lengkap = "Tidak ada waktu"
                isi_berita = "Tidak dapat diambil"

                # Ambil isi berita dan waktu dari halaman detail
                article_response = requests.get(link, headers=headers)
                if article_response.status_code == 200:
                    article_soup = BeautifulSoup(article_response.text, "html.parser")
                    
                    # Waktu terbit
                    time_tag = article_soup.find("div", class_="read__time")
                    if time_tag:
                        raw_time = time_tag.get_text(strip=True)
                        match = re.search(r"\d{2}:\d{2}\sWIB", raw_time)
                        waktu_lengkap = match.group(0) if match else "Tidak ada waktu"

                    # Isi berita
                    content_div = article_soup.find("div", class_="read__content")
                    if content_div:
                        paragraphs = content_div.find_all("p")
                        isi_berita = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

                all_data.append({
                    "judul": title,
                    "tanggal": date,
                    "waktu": waktu_lengkap,
                    "link": link,
                    "isi": isi_berita
                })

                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Error parsing article: {e}")

        # Cek apakah ada halaman berikutnya
        pagination_next = soup.find("a", class_="paging__link--next")
        if not pagination_next:
            print("✅ Tidak ada halaman berikutnya. Selesai.")
            break

        page += 1
        time.sleep(1)

    return all_data

def save_to_mongodb(data, db_name="berita_gabungan", collection_name="pencurian_minimarket_v2"):
    try:
        client = MongoClient("mongodb+srv://user1:user1_12345@database1.gfiled1.mongodb.net/?retryWrites=true&w=majority&appName=database1")
        db = client[db_name]
        collection = db[collection_name]

        inserted = 0
        for item in data:
            result = collection.update_one(
                {"link": item["link"]},
                {"$set": item},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1

        print(f"{inserted} data baru berhasil ditambahkan")
    except Exception as e:
        print(f"Error saat menyimpan ke MongoDB: {e}")

if __name__ == "__main__":
    berita = scrape_kompas_crime()
    save_to_mongodb(berita)

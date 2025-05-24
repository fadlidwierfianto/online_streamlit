import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient

# Koneksi ke MongoDB
client = MongoClient("mongodb+srv://user1:user1_12345@database1.gfiled1.mongodb.net/?retryWrites=true&w=majority&appName=database1")
db = client['berita_gabungan']
collection = db['pencurian_minimarket_v2']

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

jumlah_diperbarui = 0
jumlah_baru = 0
page = 1

while True:
    url = f'https://www.detik.com/tag/pencurian-minimarket/?sortby=time&page={page}'
    print(f'📄 Mengambil halaman: {url}')
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('article')

    if not articles:
        print("🚫 Tidak ada artikel ditemukan. Menghentikan scraping.")
        break

    for art in articles:
        link_tag = art.find('a')
        title_tag = art.find('h2', class_='title')
        date_span = art.find('span', class_='date')

        if link_tag and title_tag and date_span:
            title = title_tag.get_text(strip=True)
            link = link_tag['href']
            date_text = date_span.get_text(strip=True)

            try:
                parts = date_text.split(',')
                datetime_part = parts[1].strip() if len(parts) > 1 else ''
                date_parts = datetime_part.rsplit(' ', 3)
                if len(date_parts) == 4:
                    tanggal = ' '.join(date_parts[:2])
                    waktu = ' '.join(date_parts[2:4])
                else:
                    tanggal = datetime_part
                    waktu = ''
            except Exception:
                tanggal, waktu = '', ''

            # Ambil isi berita dari halaman detail
            try:
                detail_res = requests.get(link, headers=headers)
                detail_soup = BeautifulSoup(detail_res.content, 'html.parser')
                body_div = detail_soup.find('div', class_='detail__body-text itp_bodycontent')
                isi_berita = body_div.get_text(separator='\n', strip=True) if body_div else ''
            except Exception as e:
                print(f"⚠️ Gagal mengambil isi berita dari {link}: {e}")
                isi_berita = ''

            berita = {
                'judul': title,
                'link': link,
                'tanggal': tanggal,
                'waktu': waktu,
                'isi': isi_berita
            }

            result = collection.update_one(
                {'link': link},
                {'$set': berita},
                upsert=True
            )
            if result.matched_count > 0:
                jumlah_diperbarui += 1
            else:
                jumlah_baru += 1

    # Cek apakah ada halaman berikutnya
    pagination = soup.find('div', class_='paging')
    next_page_exists = False

    if pagination:
        pages = pagination.find_all('a')
        for p in pages:
            try:
                if int(p.get_text()) > page:
                    next_page_exists = True
                    break
            except ValueError:
                continue

    if not next_page_exists:
        print("✅ Tidak ada halaman berikutnya. Selesai.")
        break

    page += 1
    time.sleep(1)

print(f"\n✅ Selesai! {jumlah_baru} berita baru disimpan, {jumlah_diperbarui} diperbarui.")

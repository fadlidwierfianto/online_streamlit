import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import calendar
import re
from collections import Counter


# --- Koneksi ke MongoDB ---
client = MongoClient("mongodb+srv://user1:user1_12345@database1.gfiled1.mongodb.net/?retryWrites=true&w=majority&appName=database1")
db = client['berita_gabungan']
collection = db['pencurian_minimarket_v2']

# Ambil data
data = list(collection.find())
df = pd.DataFrame(data)

# --- Cek kolom penting ---
if 'tanggal' not in df.columns or 'waktu' not in df.columns:
    st.error("Kolom 'tanggal' atau 'waktu' tidak ditemukan.")
    st.stop()

# --- Konversi tanggal Indonesia ke datetime ---
bulan_mapping = {
    "januari": "01", "jan": "01",
    "februari": "02", "feb": "02",
    "maret": "03", "mar": "03",
    "april": "04", "apr": "04",
    "mei": "05",
    "juni": "06", "jun": "06",
    "juli": "07", "jul": "07",
    "agustus": "08", "agu": "08",
    "september": "09", "sep": "09",
    "oktober": "10", "okt": "10",
    "november": "11", "nov": "11",
    "desember": "12", "des": "12"
}

def ubah_tanggal(tanggal_str):
    if not isinstance(tanggal_str, str):
        return pd.NaT
    tanggal_str = tanggal_str.lower()
    for indo, angka in bulan_mapping.items():
        if re.search(rf"\b{indo}\b", tanggal_str):
            tanggal_str = re.sub(rf"\b{indo}\b", angka, tanggal_str)
            break
    try:
        return pd.to_datetime(tanggal_str, format="%d %m %Y")
    except:
        return pd.NaT

df['tanggal'] = df['tanggal'].apply(ubah_tanggal)
df['bulan'] = df['tanggal'].dt.month
df['tahun'] = df['tanggal'].dt.year

# Hapus data kosong
df = df.dropna(subset=['tanggal', 'waktu'])

# --- Grafik 1: Waktu Kejadian ---
st.header("📚 Grafik Kemunculan Kata Pagi, Siang, Sore, Malam di Isi Berita")

# Gabungkan semua isi menjadi satu teks
isi_teks = " ".join(df["isi"].dropna().astype(str)).lower()

# Hitung kemunculan kata
keywords = ["pagi", "siang", "sore", "malam"]
counts = Counter()
for kata in keywords:
    # Menghitung kemunculan kata utuh menggunakan regex
    counts[kata] = len(re.findall(rf"\b{kata}\b", isi_teks))

# Plot
fig_kata, ax_kata = plt.subplots()
ax_kata.bar(counts.keys(), counts.values(), color="coral")
ax_kata.set_xlabel("Kata")
ax_kata.set_ylabel("Jumlah Kemunculan")
ax_kata.set_title("Frekuensi Kata Waktu dalam Kolom Isi Berita")
st.pyplot(fig_kata)

# --- Grafik Gabungan: Tahun -> Bulan ---
st.header("📅 Grafik Kriminalitas per Tahun dan Bulan")

# Grafik per Tahun
tahun_counts = df['tahun'].value_counts().sort_index()

fig_tahun, ax_tahun = plt.subplots(figsize=(8, 5))
ax_tahun.bar(tahun_counts.index.astype(str), tahun_counts.values, color='skyblue')
ax_tahun.set_xlabel("Tahun")
ax_tahun.set_ylabel("Jumlah Artikel")
ax_tahun.set_title("Jumlah Kriminalitas per Tahun")
st.pyplot(fig_tahun)

# Pilih tahun untuk detail bulanan
tahun_terpilih = st.selectbox("Pilih Tahun untuk Melihat Rincian per Bulan", tahun_counts.index.sort_values())

# Filter dan tampilkan grafik per bulan
df_bulan_terpilih = df[df['tahun'] == tahun_terpilih]
bulan_counts = df_bulan_terpilih['bulan'].value_counts().sort_index()
bulan_labels = [calendar.month_name[i] for i in bulan_counts.index]

fig_bulan, ax_bulan = plt.subplots(figsize=(10, 5))
ax_bulan.plot(bulan_labels, bulan_counts.values, marker='o', color='green')
ax_bulan.set_xlabel("Bulan")
ax_bulan.set_ylabel("Jumlah Artikel")
ax_bulan.set_title(f"Jumlah Kriminalitas Tahun {tahun_terpilih} per Bulan")
ax_bulan.set_xticklabels(bulan_labels, rotation=45)

from matplotlib.ticker import MaxNLocator
ax_bulan.yaxis.set_major_locator(MaxNLocator(integer=True))  # Tampilkan hanya angka bulat

st.pyplot(fig_bulan)

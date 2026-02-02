import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

nama_file = 'Data_Akmd_Bali.xlsx'

try:
    df = pd.read_excel(nama_file)
    print(f"✅ Berhasil membaca {len(df)} data.")
except FileNotFoundError:
    print(f"❌ File '{nama_file}' tidak ditemukan.")
    exit()

df['Nama Akomodasi'] = df['Nama Akomodasi'].astype(str)
df['Lokasi'] = df['Lokasi'].astype(str)
df['Wilayah'] = df['Wilayah'].astype(str)

geolocator = Nominatim(user_agent="pencari_akomodasi", timeout=20)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5,
                      max_retries=3, error_wait_seconds=5)

total_data = len(df)
counter = 0

print("\n Memulai Mencari Koordinat...")


def cari_koordinat_bertingkat(row):
    global counter
    counter += 1

    nama_akmd = row['Nama Akomodasi']
    lokasi = row['Lokasi']
    wilayah = row['Wilayah']

    persen = (counter / total_data) * 100
    print(
        f"[{counter}/{total_data}] {persen:.1f}% | Cek: {nama_akmd[:25]}...", end="\r")

    hasil = None

    try:
        query_1 = f"{nama_akmd}, {lokasi}, {wilayah}"
        hasil = geocode(query_1)

        if hasil is None:
            query_2 = f"{lokasi}, {wilayah}"
            hasil = geocode(query_2)

        if hasil:
            return pd.Series([hasil.latitude, hasil.longitude])
        else:
            return pd.Series([None, None])
    except Exception:
        return pd.Series([None, None])


df[['Latitude', 'Longitude']] = df.apply(cari_koordinat_bertingkat, axis=1)

print("\n\n" + "="*50)
print("Membersihkan data yang tidak ketemu...")

df_final = df.dropna(subset=['Latitude', 'Longitude'])

jumlah_awal = total_data
jumlah_akhir = len(df_final)
jumlah_dibuang = jumlah_awal - jumlah_akhir

print(f"Total Awal    : {jumlah_awal}")
print(f"Disimpan      : {jumlah_akhir}")
print(f"Dihapus       : {jumlah_dibuang} (Karena lokasi tidak ketemu)")

nama_output = "Data_Akmd_Bali_Koordinat.xlsx"
df_final.to_excel(nama_output, index=False)
print(f"💾 File Bersih Tersimpan: {nama_output}")
print("="*50)

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# 1. BUKA FILE YANG LENGKAP (1300 Data)
# Pastikan ini nama file hasil scraping (bukan hasil gis yang 800)
nama_file = 'Data_Hotel_Bali.xlsx' 

try:
    df = pd.read_excel(nama_file)
    print(f"✅ Berhasil membaca {len(df)} data mentah.")
except FileNotFoundError:
    print("❌ File tidak ditemukan. Pastikan nama file benar.")
    exit()

# 2. CONFIG
geolocator = Nominatim(user_agent="pencari_bertahap_v1", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.2)

nama_kolom_alamat = 'Lokasi' if 'Lokasi' in df.columns else 'Alamat'
total_data = len(df)
counter = 0
sukses_counter = 0

print("\n🛡️ Memulai Geocoding Bertingkat...")
print("   Strategi: Jika Hotel tidak ketemu, kita ambil titik tengah Wilayahnya.")

# 3. FUNGSI PENCARI PINTAR
def cari_koordinat_bertingkat(row):
    global counter, sukses_counter
    counter += 1
    
    nama_hotel = row['Nama Hotel']
    lokasi_asli = row[nama_kolom_alamat]
    
    # Bersihkan lokasi dari kata-kata aneh (misal: "2.5 km dari pusat")
    # Kita ambil kata pertama saja sebagai wilayah utama jika string terlalu panjang
    lokasi_bersih = lokasi_asli.split(',')[0] 

    print(f"[{counter}/{total_data}] 🔎 {nama_hotel[:20]}...", end="\r") 
    
    hasil = None
    
    try:
        # TAHAP 1: Cari Spesifik (Nama Hotel + Lokasi)
        query_1 = f"{nama_hotel}, {lokasi_asli}, Bali"
        hasil = geocode(query_1)
        
        # TAHAP 2: Jika Gagal, Cari Lokasinya Saja (Misal: "Canggu, Bali")
        if hasil is None:
            query_2 = f"{lokasi_asli}, Bali"
            hasil = geocode(query_2)
            
        # TAHAP 3: Jika Masih Gagal, Cari Kata Kunci Wilayah Saja
        if hasil is None:
             query_3 = f"{lokasi_bersih}, Bali"
             hasil = geocode(query_3)

        if hasil:
            sukses_counter += 1
            return pd.Series([hasil.latitude, hasil.longitude, "Sukses"])
        else:
            return pd.Series([None, None, "Gagal"])

    except Exception:
        return pd.Series([None, None, "Error"])

# 4. EKSEKUSI
df[['Latitude', 'Longitude', 'Status_GIS']] = df.apply(cari_koordinat_bertingkat, axis=1)

# 5. SIMPAN HASIL
print("\n\n✅ Proses Selesai!")

# Kita lihat berapa yang sukses
df_final = df.dropna(subset=['Latitude', 'Longitude'])
jumlah_sukses = len(df_final)

print(f"📊 Laporan Akhir:")
print(f"   - Total Data Awal: {total_data}")
print(f"   - Berhasil Geocoding: {jumlah_sukses}")
print(f"   - Gagal: {total_data - jumlah_sukses}")

if jumlah_sukses >= 1000:
    print("\n🎉 SELAMAT! Target 1000 data tercapai.")
else:
    print("\n⚠️ Masih kurang. Coba cek koneksi atau scrap lebih banyak.")

df_final.to_excel("Data_Hotel_Bali_Koordinat.xlsx", index=False)
print("📁 File disimpan: Data_Hotel_Bali_Koordinat.xlsx")
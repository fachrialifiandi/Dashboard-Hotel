from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime, timedelta

# --- SETTING TANGGAL (Wajib) ---
besok = datetime.now() + timedelta(days=14)
lusa = besok + timedelta(days=1)
str_checkin = besok.strftime("%Y-%m-%d")
str_checkout = lusa.strftime("%Y-%m-%d")

# --- SETUP BROWSER ---
options = Options()
# options.add_argument("--headless") # Aktifkan nanti kalau sudah yakin jalan
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=options)

all_data = []
target_data = 1300
offset = 0

print(f"🚀 Mulai Scraping: Hanya mengambil data dengan Rating > 0")

try:
    while len(all_data) < target_data:
        url = (f"https://www.booking.com/searchresults.id.html"
               f"?ss=Bali&checkin={str_checkin}&checkout={str_checkout}"
               f"&group_adults=2&no_rooms=1&group_children=0&offset={offset}")

        driver.get(url)
        time.sleep(4)  # Tunggu loading

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.select('[data-testid="property-card"]')

        if not cards:
            print("⚠️ Data habis di website. Berhenti.")
            break

        print(
            f"🔄 Scanning halaman offset {offset}... (Total tersimpan saat ini: {len(all_data)})")

        for card in cards:
            if len(all_data) >= target_data:
                print("✅ Target 1000 data tercapai!")
                break

            try:
                # 1. RATING (Kita cek ini DULUAN)
                rating = 0
                try:
                    rating_el = card.select_one('[data-testid="review-score"]')
                    if rating_el:
                        rating_text = rating_el.get_text(strip=True)
                        match = re.search(r"(\d+[.,]\d+)", rating_text)
                        if match:
                            rating = float(match.group(1).replace(',', '.'))
                except:
                    rating = 0

                # --- FILTER PENTING DI SINI ---
                if rating == 0:
                    # Jika rating 0, langsung skip ke hotel berikutnya
                    continue
                # ------------------------------

                # 2. NAMA
                nama_el = card.select_one('[data-testid="title"]')
                nama = nama_el.get_text(
                    strip=True) if nama_el else "Tanpa Nama"

                # 3. HARGA
                try:
                    harga_el = card.select_one(
                        '[data-testid="price-and-discounted-price"]')
                    if harga_el:
                        harga_text = harga_el.get_text(strip=True)
                        harga = int(''.join(filter(str.isdigit, harga_text)))
                    else:
                        harga = 0
                except:
                    harga = 0

                # 4. LOKASI
                lokasi_el = card.select_one('[data-testid="address"]')
                lokasi = lokasi_el.get_text(
                    strip=True) if lokasi_el else "Bali"

                # Simpan Data (Hanya jika lolos filter rating)
                all_data.append({
                    'Nama Hotel': nama,
                    'Harga': harga,
                    'Lokasi': lokasi,
                    'Rating': rating
                })

            except Exception as e:
                continue

        # Logika Pindah Halaman
        offset += 25

finally:
    driver.quit()

    # Simpan ke Excel
    if len(all_data) > 0:
        df = pd.DataFrame(all_data)
        filename = "Data_Hotel_Bali.xlsx"
        df.to_excel(filename, index=False)
        print(
            f"✅ Selesai! {len(all_data)} Data bersih (tanpa rating 0) disimpan di {filename}")
    else:
        print("❌ Tidak ada data yang tersimpan.")

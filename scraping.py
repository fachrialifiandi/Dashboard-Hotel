from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime, timedelta


target_total = 2200
daftar_wilayah = [
    "Kuta Bali", "Denpasar", "Canggu", "Sanur", "Jimbaran", "Ubud"
]


besok = datetime.now() + timedelta(days=1)
lusa = besok + timedelta(days=1)
str_checkin = besok.strftime("%Y-%m-%d")
str_checkout = lusa.strftime("%Y-%m-%d")

options = Options()

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=options)
actions = ActionChains(driver)
wait = WebDriverWait(driver, 15)

all_data = []
seen_akmds = set()

print("="*30)
print(f"MEMULAI SCRAPING")
print(f"Target: {target_total} Akomodasi")
print("="*30)

try:
    for wilayah in daftar_wilayah:
        if len(all_data) >= target_total:
            print("\n TARGET TOTAL TERCAPAI! ")
            break

        print(f"\n📍 Wilayah: {wilayah.upper()}...")

        url = (f"https://www.booking.com/searchresults.id.html"
               f"?ss={wilayah}&checkin={str_checkin}&checkout={str_checkout}"
               f"&group_adults=2&no_rooms=1&group_children=0")

        try:
            driver.get(url)
            time.sleep(5)
        except Exception as e:
            print(f"   ⚠️ Gagal load URL: {e}")
            continue

        limit_klik = 0
        max_klik_per_wilayah = 30

        while limit_klik < max_klik_per_wilayah:

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.select('[data-testid="property-card"]')

            data_baru_count = 0

            for card in cards:
                try:

                    nama_el = card.select_one('[data-testid="title"]')
                    nama = nama_el.get_text(
                        strip=True) if nama_el else "Tanpa Nama"

                    lokasi_el = card.select_one('[data-testid="address"]')
                    lokasi = lokasi_el.get_text(
                        strip=True) if lokasi_el else wilayah

                    unique_key = (nama, lokasi)
                    if unique_key in seen_akmds:
                        continue

                    rating = 0.0
                    try:
                        rating_el = card.select_one(
                            '[data-testid="review-score"]')
                        if rating_el:
                            txt = rating_el.get_text(strip=True)
                            match = re.search(r"(\d+[.,]\d+)", txt)
                            if match:
                                rating = float(
                                    match.group(1).replace(',', '.'))
                    except:
                        pass

                    harga = 0
                    try:
                        harga_el = card.select_one(
                            '[data-testid="price-and-discounted-price"]')
                        if not harga_el:
                            harga_el = card.select_one(
                                '.bui-price-display__value')

                        if harga_el:
                            txt_harga = harga_el.get_text(strip=True)
                            harga = int(
                                ''.join(filter(str.isdigit, txt_harga)))
                    except:
                        pass

                    # Simpan
                    all_data.append({
                        'Nama Akomodasi': nama,
                        'Harga': harga,
                        'Lokasi': lokasi,
                        'Rating': rating,
                        'Wilayah': wilayah
                    })
                    seen_akmds.add(unique_key)
                    data_baru_count += 1

                except Exception:
                    continue

            print(
                f"   --> Total: {len(all_data)} | Baru: {data_baru_count} | Akomodasi Terakhir: {nama[:15]}...")

            if len(all_data) >= target_total:
                break

            try:

                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
                time.sleep(2)

                driver.find_element(
                    By.TAG_NAME, 'body').send_keys(Keys.PAGE_UP)
                time.sleep(1)

                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
                time.sleep(1)

                xpath_tombol = (
                    "//button[@data-testid='load-more-results-button'] | "
                    "//button[contains(., 'Muat hasil lainnya')] | "
                    "//button[contains(., 'Tampilkan hasil lainnya')] | "
                    "//button[contains(., 'Show more results')]"
                )

                try:

                    tombol = wait.until(
                        EC.element_to_be_clickable((By.XPATH, xpath_tombol)))

                    actions.move_to_element(tombol).perform()
                    time.sleep(1)

                    tombol.send_keys(Keys.ENTER)

                    time.sleep(8)
                    limit_klik += 1

                except TimeoutException:
                    print(
                        f" ⚠️ Mungkin data habis")
                    break

            except Exception as e:
                print(f"   🛑 Error Navigasi: {e}")
                break

finally:
    driver.quit()

    if len(all_data) > 0:
        df = pd.DataFrame(all_data)

        df_clean = df.drop_duplicates(subset=['Nama Akomodasi', 'Lokasi'])
        filename = (f"Data_Akmd_Bali.xlsx")
        df_clean.to_excel(filename, index=False)

        print("\n" + "="*60)
        print(f"✅ SCRAPING SELESAI!")
        print(f" File Excel: {filename}")
        print(f" Total Akomodasi: {len(df_clean)}")
        print("="*60)
    else:
        print("❌ Tidak ada data yang tersimpan.")

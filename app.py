import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Akomodasi GIS Dashboard",
    page_icon="🗺️",
    layout="wide"
)


@st.cache_data
def load_data():
    file_path = 'Data_Akmd_Bali_Koordinat.xlsx'

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(
            f"❌ File '{file_path}' tidak ditemukan! Pastikan file ada di folder yang sama.")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    cols_to_numeric = ['Rating', 'Latitude', 'Longitude', 'Harga']
    for col in cols_to_numeric:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(
                    ',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df = df.dropna(subset=['Latitude', 'Longitude'])

    return df


df = load_data()


def kategori_harga(harga):
    if pd.isna(harga):
        return 'Tanpa Harga'
    if harga < 500000:
        return 'Budget (< 500rb)'
    elif harga <= 2000000:
        return 'Menengah (500rb - 2jt)'
    else:
        return 'Mewah (> 2jt)'


def kategori_rating(rating):
    if pd.isna(rating):
        return 'Tanpa Rating'
    if rating >= 9.0:
        return 'Luar Biasa (9+)'
    elif rating >= 8.0:
        return 'Sangat Baik (8-9)'
    else:
        return 'Baik (< 8)'


with st.sidebar:
    st.header("🔍 Filter Pencarian")
    st.info("Atur filter lalu klik tombol 'Terapkan'.")

    if not df.empty:
        with st.form("filter_form"):
            if 'Wilayah' in df.columns:
                lokasi_list = sorted(
                    df['Wilayah'].astype(str).unique().tolist())
                selected_lokasi = st.multiselect(
                    "Pilih Wilayah", lokasi_list, default=[])
            else:
                selected_lokasi = []

            if 'Harga' in df.columns:
                max_price_data = int(
                    df['Harga'].max()) if not df['Harga'].isnull().all() else 15000000
                price_range = st.slider(
                    "Rentang Harga per Malam (IDR)",
                    min_value=0,
                    max_value=max_price_data,
                    value=(0, max_price_data),
                    step=50000,
                    format="%d"
                )
            else:
                price_range = (0, 0)

            if 'Rating' in df.columns:
                min_rating = st.slider(
                    "Minimum Rating", 0.0, 10.0, 7.0, step=0.1)
            else:
                min_rating = 0

            st.markdown("---")
            submitted = st.form_submit_button("✅ Terapkan Filter")
    else:
        st.warning("Data belum dimuat.")
        selected_lokasi = []
        price_range = (0, 0)
        min_rating = 0
        submitted = False


filtered_df = df.copy()

if not filtered_df.empty:
    if selected_lokasi:
        filtered_df = filtered_df[filtered_df['Lokasi'].isin(selected_lokasi)]

    if 'Harga' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Harga'].between(
            price_range[0], price_range[1])]

    if 'Rating' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Rating'] >= min_rating]


st.title("🏨 Dashboard Akomodasi Bali")

if not df.empty:
    min_p_str = f"{price_range[0]:,.0f}".replace(",", ".")
    max_p_str = f"{price_range[1]:,.0f}".replace(",", ".")

    st.caption(
        f"📍 Wilayah: **{'Semua' if not selected_lokasi else ', '.join(selected_lokasi)}** | "
        f"💰 Harga: **Rp {min_p_str} - Rp {max_p_str}**"
    )

    with st.container(border=True):
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Akomodasi", f"{len(filtered_df)} Unit")

        if not filtered_df.empty:
            if 'Harga' in filtered_df.columns:
                rata_harga = filtered_df['Harga'].mean()
                kpi2.metric("Rata-rata Harga",
                            f"Rp {rata_harga:,.0f}".replace(",", "."))
            if 'Rating' in filtered_df.columns:
                rata_rating = filtered_df['Rating'].mean()
                kpi3.metric("Rata-rata Rating", f"{rata_rating:.1f} ⭐")
        else:
            kpi2.metric("Rata-rata Harga", "-")
            kpi3.metric("Rata-rata Rating", "-")

    tab1, tab2, tab3 = st.tabs(
        ["🗺️ Peta Sebaran", "📊 Analisis Proporsi", "📋 Data Tabel"])

    with tab1:
        if not filtered_df.empty:
            avg_lat = filtered_df['Latitude'].mean()
            avg_lon = filtered_df['Longitude'].mean()
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11)

            for _, row in filtered_df.iterrows():
                harga = row.get('Harga', 0)
                color = 'green' if harga < 1000000 else 'orange' if harga < 3000000 else 'red'
                harga_fmt = f"{harga:,.0f}".replace(",", ".")

                popup_html = f"""
                <b>{row['Nama Akomodasi']}</b><br>
                Rp {harga_fmt}<br>
                Rating: {row['Rating']}
                """

                folium.Marker(
                    [row['Latitude'], row['Longitude']],
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=row['Nama Akomodasi'],
                    icon=folium.Icon(color=color, icon="bed", prefix="fa")
                ).add_to(m)

            st_folium(m, use_container_width=True, height=500)
            st.caption("🟢 < 500rb |🟠 500rb - 1.5jt | 🔴 > 1.5jt")
        else:
            st.warning("Tidak ada data yang sesuai filter.")

    with tab2:
        if not filtered_df.empty:
            st.subheader(" Statistik Proporsi Akomodasi")

            col_p1, col_p2 = st.columns(2)

            with col_p1:
                filtered_df['Kat_Harga'] = filtered_df['Harga'].apply(
                    kategori_harga)
                pie_harga_df = filtered_df['Kat_Harga'].value_counts(
                ).reset_index()
                pie_harga_df.columns = ['Kategori', 'Jumlah']

                fig_pie1 = px.pie(
                    pie_harga_df,
                    values='Jumlah',
                    names='Kategori',
                    title='Berdasarkan Range Harga',
                    hole=0.4,
                    color='Kategori',
                    color_discrete_map={
                        'Budget (< 500rb)': '#2ecc71',
                        'Menengah (500rb - 2jt)': '#f1c40f',
                        'Mewah (> 2jt)': '#e74c3c'
                    }
                )
                st.plotly_chart(fig_pie1, use_container_width=True)

            with col_p2:
                filtered_df['Kat_Rating'] = filtered_df['Rating'].apply(
                    kategori_rating)

                bar_rating = filtered_df['Kat_Rating'].value_counts(
                ).reset_index()
                bar_rating.columns = ['Kategori', 'Jumlah']

                peta_warna_rating = {
                    'Luar Biasa (9+)': '#2ecc71',
                    'Sangat Baik (8-9)': '#f1c40f',
                    'Baik (< 8)': '#e74c3c',
                    'Tanpa Rating': '#95a5a6'
                }

                fig2 = px.bar(
                    bar_rating,
                    x='Kategori',
                    y='Jumlah',
                    title='Distribusi Rating',
                    color='Kategori',
                    color_discrete_map=peta_warna_rating

                )

                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("Data kosong.")

    with tab3:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Harga": st.column_config.NumberColumn(
                    "Harga (IDR)", format="Rp %.0f"
                ),
                "Rating": st.column_config.NumberColumn(
                    "Rating", format="%.1f ⭐"
                )
            }
        )
else:
    st.error("Data tidak ditemukan. Silakan upload file 'Data_Akmd_Bali_Koordinat.xlsx' ke folder yang sama.")

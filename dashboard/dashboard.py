import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import folium
from babel.numbers import format_currency
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Set style seaborn
sns.set(style='dark')

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "payment_value": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value": "revenue"
    }, inplace=True)
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_id.count().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_review_scores_df(df):
    review_scores_df = df['review_score'].value_counts().sort_index().reset_index()
    review_scores_df.columns = ['review_score', 'count']
    return review_scores_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", # Mengambil tanggal order terakhir
        "order_id": "nunique",
        "payment_value": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

# ==========================================
# LOAD DATA
# ==========================================
# Load data utama
#all_df = pd.read_csv("all_data.csv")
all_df = pd.read_csv("https://github.com/mpnabil95/Data_Analyst_Project-_E-Commerce_Public_Dataset/blob/29459b74e3c34a820b3b518b356c8e53423dc754/dashboard/all_data.csv?raw=true")

# Load data geolokasi untuk peta
#geo_df = pd.read_csv("geolocation_dataset.csv")
geo_df = pd.read_csv("https://github.com/mpnabil95/Data_Analyst_Project-_E-Commerce_Public_Dataset/blob/29459b74e3c34a820b3b518b356c8e53423dc754/dashboard/geolocation_dataset.csv?raw=true")

# Membersihkan data geolokasi (Drop duplicates)
geo_df.drop_duplicates(subset='geolocation_zip_code_prefix', keep='first', inplace=True)

# Mengubah tipe data tanggal
datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Mengurutkan data berdasarkan order_purchase_timestamp
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(drop=True, inplace=True)

# ==========================================
# SIDEBAR & FILTER
# ==========================================
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    st.markdown("### Filter Data")
    # Rentang Waktu
    start_date, end_date = st.date_input(
        label='Rentang Waktu:',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Memfilter data utama berdasarkan input dari sidebar
main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# Menyiapkan berbagai dataframe untuk visualisasi menggunakan helper functions
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
review_scores_df = create_review_scores_df(main_df)
rfm_df = create_rfm_df(main_df)

# ==========================================
# DASHBOARD UTAMA
# ==========================================
st.title('E-Commerce Public Dashboard 🛒')
st.markdown("---")

# ------------------------------------------
# 1. VISUALISASI PERFORMA PENJUALAN (TIME SERIES)
# ------------------------------------------
st.subheader('1. Performa Penjualan Seiring Waktu')

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Orders", value=daily_orders_df.order_count.sum())
with col2:
    st.metric("Total Revenue", value=format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR'))

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"], marker='o', linewidth=2, color="#72BCD4")
ax.set_ylabel("Jumlah Pesanan", fontsize=15)
ax.set_xlabel("Tanggal", fontsize=15)
ax.tick_params(axis='y', labelsize=12)
ax.tick_params(axis='x', labelsize=12, rotation=45)
ax.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig)

# ------------------------------------------
# 2. VISUALISASI PERFORMA PRODUK
# ------------------------------------------
st.subheader("2. Produk Paling Laris & Paling Sedikit Terjual")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_id", y="product_category_name_english", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Jumlah Penjualan", fontsize=15)
ax[0].set_title("5 Kategori Produk Paling Laris", loc="center", fontsize=18)
ax[0].tick_params(axis='y', labelsize=15)

sns.barplot(x="order_id", y="product_category_name_english", data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Jumlah Penjualan", fontsize=15)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("5 Kategori Produk Paling Sedikit Terjual", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)
st.pyplot(fig)

# ------------------------------------------
# 3. VISUALISASI KEPUASAN PELANGGAN
# ------------------------------------------
st.subheader("3. Tingkat Kepuasan Pelanggan (Review Scores)")

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x='review_score', y='count', data=review_scores_df, palette=["#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#72BCD4"])
ax.set_title("Distribusi Skor Ulasan Pelanggan", fontsize=15)
ax.set_xlabel("Skor Bintang", fontsize=12)
ax.set_ylabel("Jumlah Ulasan", fontsize=12)
for index, row in review_scores_df.iterrows():
    ax.text(row.name, row['count'] + 500, str(row['count']), ha='center', fontsize=10)
st.pyplot(fig)

# ------------------------------------------
# 4. VISUALISASI GEOSPATIAL (PETA)
# ------------------------------------------
st.subheader("4. Demografi Pelanggan (Geospatial Analysis)")

# Merge main_df dengan geo_df untuk mendapatkan koordinat
cust_geo_df = pd.merge(
    left=main_df,
    right=geo_df,
    how="inner",
    left_on="customer_zip_code_prefix",
    right_on="geolocation_zip_code_prefix"
)
# Filter bounding box Brazil
brazil_geo = cust_geo_df[
    (cust_geo_df['geolocation_lat'] <= 5.274388) & 
    (cust_geo_df['geolocation_lat'] >= -33.751169) & 
    (cust_geo_df['geolocation_lng'] <= -34.710462) & 
    (cust_geo_df['geolocation_lng'] >= -73.9828305)
]

# Membuat peta interaktif dengan Folium
brazil_map = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
heat_data = brazil_geo[['geolocation_lat', 'geolocation_lng']].values.tolist()
HeatMap(heat_data, radius=15, blur=10).add_to(brazil_map)

# Menampilkan peta Folium di Streamlit
st_folium(brazil_map, width=800, height=500)

# ------------------------------------------
# 5. VISUALISASI RFM ANALYSIS
# ------------------------------------------
st.subheader("5. Analisis RFM (Recency, Frequency, Monetary)")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Recency (days)", value=round(rfm_df.recency.mean(), 1))
with col2:
    st.metric("Average Frequency", value=round(rfm_df.frequency.mean(), 2))
with col3:
    st.metric("Average Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 8))
colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]

sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Customer ID", fontsize=15)
ax[0].set_title("By Recency (days)", loc="center", fontsize=20)
ax[0].tick_params(axis='x', rotation=45, labelsize=12)

sns.barplot(y="frequency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Customer ID", fontsize=15)
ax[1].set_title("By Frequency", loc="center", fontsize=20)
ax[1].tick_params(axis='x', rotation=45, labelsize=12)

sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("Customer ID", fontsize=15)
ax[2].set_title("By Monetary", loc="center", fontsize=20)
ax[2].tick_params(axis='x', rotation=45, labelsize=12)

st.pyplot(fig)

st.caption('Copyright (C) 2026')

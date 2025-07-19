import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Konfigurasi dan Pemuatan Data ---
st.set_page_config(
    page_title="Analisis Kinerja E-commerce",
    layout="wide"
)

@st.cache_data
def load_data():
    """Memuat semua dataset yang diperlukan dari direktori 'E-commerce/'."""
    path = "E-commerce/"
    try:
        payments = pd.read_csv(path + "order_payments_dataset.csv")
        customers = pd.read_csv(path + "customers_dataset.csv")
        # <-- MODIFIKASI: Menambahkan parse_dates untuk orders -->
        orders = pd.read_csv(path + "orders_dataset.csv", parse_dates=['order_purchase_timestamp'])
        sellers = pd.read_csv(path + "sellers_dataset.csv")
        products = pd.read_csv(path + "products_dataset.csv")
        order_items = pd.read_csv(path + "order_items_dataset.csv")
        order_reviews = pd.read_csv(path + "order_reviews_dataset.csv")
    except FileNotFoundError as e:
        st.error(f"Error: Salah satu file dataset tidak ditemukan di '{path}'. Pastikan semua file ada.")
        st.stop()
    return payments, customers, orders, sellers, products, order_items, order_reviews


# Memuat data
payments, customers, orders, sellers, products, order_items, order_reviews = load_data()

# --- 2. Judul dan Kalimat Pembuka ---
st.title("📈 Analisis Kinerja Bisnis E-commerce")
st.markdown("""
Dasbor ini dirancang untuk mengungkap wawasan strategis dari data operasional, mencakup analisis mendalam mengenai **preferensi pelanggan**, **kualitas produk**, dan **kinerja pengiriman** untuk mendorong pertumbuhan bisnis.
""")
st.markdown("---")

# --- 3. Ringkasan Eksekutif: KPI dan Tren Pendapatan ---
st.header("Gambaran Umum Kinerja Operasional")

# <-- MODIFIKASI: Membuat tata letak 2 kolom -->
col1, col2 = st.columns([1, 2]) # Kolom kiri lebih kecil untuk KPI

with col1:
    # --- Kalkulasi metrik KPI ---
    total_revenue = payments['payment_value'].sum()
    total_customers = customers['customer_unique_id'].nunique()
    total_orders = orders['order_id'].nunique()
    total_sellers = sellers['seller_id'].nunique()
    total_products = products['product_id'].nunique()

    # --- Tampilkan KPI (sekarang di kolom kiri) ---
    st.subheader("Metrik Utama")
    
    # <-- MODIFIKASI: Menggunakan notasi angka Indonesia -->
    st.metric(
        label="Total Pendapatan (R$)",
        value=f"R$ {total_revenue/1_000_000:,.2f} Jt".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.metric(
        label="Total Pelanggan",
        value=f"{total_customers:,}".replace(",", ".")
    )
    st.metric(
        label="Total Pesanan",
        value=f"{total_orders:,}".replace(",", ".")
    )
    st.metric(
        label="Total Penjual (Seller)",
        value=f"{total_sellers:,}".replace(",", ".")
    )
    st.metric(
        label="Total Produk",
        value=f"{total_products:,}".replace(",", ".")
    )

with col2:
    # --- Grafik Tren Pendapatan (sekarang di kolom kanan) ---
    st.subheader("Tren Pendapatan Bulanan")
    
    # Gabungkan data order dan payment untuk mendapatkan tanggal dan nilai pembayaran
    revenue_over_time = orders.merge(payments, on='order_id')
    
    # Ekstrak bulan dari tanggal pembelian
    revenue_over_time['month'] = revenue_over_time['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
    
    # Agregasi pendapatan per bulan
    monthly_revenue = revenue_over_time.groupby('month')['payment_value'].sum().reset_index()
    
    # Buat grafik
    fig = px.area(
        monthly_revenue,
        x='month',
        y='payment_value',
        title="Pertumbuhan Pendapatan Seiring Waktu",
        labels={'month': 'Bulan', 'payment_value': 'Total Pendapatan (R$)'}
    )
    fig.update_layout(height=450) # Menyesuaikan tinggi grafik
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ========== BRIDGING: Narasi Transisi ==========
st.header("Eksplorasi Lebih Dalam: Preferensi Pelanggan & Dampak Ongkir")
st.markdown(
    "Selanjutnya, mari kita telusuri lebih dalam faktor-faktor kunci yang mempengaruhi preferensi pelanggan serta hubungannya dengan kepuasan dan biaya pengiriman."
)

# ========== SECTION: KATEGORI PRODUK POPULER (DUA KOLOM BERSEBELAHAN) ==========
st.subheader("Kategori Produk Paling Populer")

# Siapkan data join orders, products, customers (tambahkan join customers jika ingin filter state)
orders_items = orders.merge(pd.read_csv("E-commerce/order_items_dataset.csv"), on='order_id', how='left')

# 2. Gabungkan hasilnya dengan products berdasarkan product_id
orders_items = orders_items.merge(products, on='product_id', how='left')

# 3. Gabungkan dengan customers untuk mendapatkan provinsi (optional, jika ingin filter per state)
orders_items = orders_items.merge(customers[['customer_id', 'customer_state']], on='customer_id', how='left')


col1, col2 = st.columns(2)

# Kategori terpopuler secara keseluruhan
with col1:
    st.markdown("**Top 10 Kategori Produk (Keseluruhan)**")
    top_cats = (
        orders_items['product_category_name']
        .value_counts()
        .head(10)
        .reset_index()
    )
    # Kolom hasil: 'index' untuk kategori, 'product_category_name' untuk count
    top_cats.columns = ['Kategori', 'Jumlah Order']
    fig_top_cats = px.bar(
        top_cats,
        x='Kategori', y='Jumlah Order',
        text='Jumlah Order',
        color_discrete_sequence=["royalblue"]
    )
    fig_top_cats.update_layout(xaxis_tickangle=-45, height=350)
    st.plotly_chart(fig_top_cats, use_container_width=True)

with col2:
    st.markdown("**Top 5 Kategori Produk per Provinsi**")
    provinsi_list = sorted(orders_items['customer_state'].dropna().unique())
    pilih_state = st.selectbox("Pilih Provinsi", provinsi_list)
    top5_state = (
        orders_items[orders_items['customer_state'] == pilih_state]
        .product_category_name
        .value_counts()
        .head(5)
        .reset_index()
    )
    top5_state.columns = ['Kategori', 'Jumlah Order']
    fig_top5_state = px.bar(
        top5_state,
        x='Kategori', y='Jumlah Order',
        text='Jumlah Order',
        color_discrete_sequence=["royalblue"]
    )
    fig_top5_state.update_layout(xaxis_tickangle=-45, height=350)
    st.plotly_chart(fig_top5_state, use_container_width=True)


st.markdown("---")

# ========== SECTION: REVIEW SCORE VS FREIGHT VALUE (BAR CHART) ==========
st.subheader("Rata-Rata Review Score Berdasarkan Freight Value (Ongkir)")

df_full = (
    orders
    .merge(order_items, on='order_id', how='left')
    .merge(products, on='product_id', how='left')
    .merge(customers[['customer_id', 'customer_state']], on='customer_id', how='left')
    .merge(order_reviews[['order_id', 'review_score']], on='order_id', how='left')
)

# --- Sekarang df_full sudah punya kolom freight_value DAN review_score ---
# Binning freight_value
bins = [0, 10, 20, 30, 40, 50, float('inf')]
labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50+"]
df_full['freight_bin'] = pd.cut(df_full['freight_value'], bins=bins, labels=labels, right=False)

review_freight = (
    df_full
    .groupby('freight_bin')['review_score']
    .mean()
    .reset_index()
    .dropna()
)

fig_review = px.bar(
    review_freight, x='freight_bin', y='review_score',
    text=review_freight['review_score'].round(2),
    labels={'freight_bin': 'Freight Value (R$)', 'review_score': 'Average Review Score'},
    color_discrete_sequence=["royalblue"]
)
fig_review.update_traces(textposition='outside')
fig_review.update_layout(yaxis=dict(range=[0, 5]), title="Average Review Score Drops as Shipping Cost (Freight Value) Increases")
st.plotly_chart(fig_review, use_container_width=True)

# ========== END: Narasi Penutup ==========
st.markdown(
    """
---
Dari analisis ini, terlihat bahwa preferensi pelanggan sangat dipengaruhi oleh kategori produk tertentu yang berbeda di tiap provinsi. Selain itu, terdapat korelasi antara biaya pengiriman dan kepuasan pelanggan, yang dapat menjadi peluang insentif untuk mendorong konversi dan loyalitas pelanggan.
"""
)

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
    except FileNotFoundError as e:
        st.error(f"Error: Salah satu file dataset tidak ditemukan di '{path}'. Pastikan semua file ada.")
        st.stop()
    return payments, customers, orders, sellers, products

# Memuat data
payments, customers, orders, sellers, products = load_data()

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

# Bagian selanjutnya dari dasbor Anda akan dimulai di sini
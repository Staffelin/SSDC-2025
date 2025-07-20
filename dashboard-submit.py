import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go


# --- 1. Konfigurasi dan Pemuatan Data ---
st.set_page_config(
    page_title="Analisis Kinerja E-commerce",
    layout="wide"
)

# --- Variabel Desain Global ---
THEME_COLOR = "royalblue"
PLOTLY_TEMPLATE = "plotly_white"

@st.cache_data
def load_data():
    """Memuat semua dataset yang diperlukan dari direktori 'E-commerce/'."""
    path = "E-commerce/"
    try:
        payments = pd.read_csv(path + "order_payments_dataset.csv")
        customers = pd.read_csv(path + "customers_dataset.csv")
        orders = pd.read_csv(path + "orders_dataset.csv", parse_dates=['order_purchase_timestamp', 'order_delivered_customer_date', 'order_estimated_delivery_date'])
        sellers = pd.read_csv(path + "sellers_dataset.csv")
        products = pd.read_csv(path + "products_dataset.csv")
        order_items = pd.read_csv(path + "order_items_dataset.csv")
        deals = pd.read_csv(path + "closed_deals_dataset.csv", parse_dates=["won_date"])
        cat_trans = pd.read_csv(path + "product_category_name_translation.csv")
        reviews = pd.read_csv(path + "order_reviews_dataset_translated.csv")
        leads = pd.read_csv(path + "marketing_qualified_leads_dataset.csv", parse_dates=["first_contact_date"])

    except FileNotFoundError as e:
        st.error(f"Error: Salah satu file dataset tidak ditemukan di '{path}'. Pastikan semua file ada, termasuk 'order_reviews_dataset_translated.csv'.")
        st.stop()
    return payments, customers, orders, sellers, products, order_items, reviews, cat_trans, deals, leads

def format_snake_case(s):
    if isinstance(s, str): return s.replace('_', ' ').title()
    return s

# Memuat semua data
payments, customers, orders, sellers, products, order_items, reviews, cat_trans, deals, leads = load_data()

# --- Membuat DataFrame Utama (df_master) ---
items = order_items.merge(products, on="product_id", how="left")
items = items.merge(cat_trans, on="product_category_name", how="left")
df_master = orders.merge(reviews, on="order_id", how="left")
df_master = df_master.merge(items, on="order_id", how="left")
df_master = df_master.merge(customers, on='customer_id', how='left')
df_master['product_category_name_english'] = df_master['product_category_name_english'].dropna().apply(format_snake_case)

# --- MULAI DASBOR ---

# --- 2. Judul dan Kalimat Pembuka ---
st.title("📈 Analisis Kinerja Bisnis E-commerce")
st.markdown("Dasbor ini dirancang untuk mengungkap wawasan strategis dari data operasional, mencakup analisis mendalam mengenai **preferensi pelanggan**, **kualitas produk**, dan **kinerja pengiriman** untuk mendorong pertumbuhan bisnis.")
st.markdown("---")

# --- 3. Ringkasan Eksekutif: KPI dan Tren Pendapatan ---
st.header("Pertumbuhan Volume Tidak Lagi Cukup: Skala Besar, Tantangan Lebih Besar")
st.markdown("Hampir 100.000 pesanan dan 96.000 pelanggan mencerminkan skala operasional yang luas, namun belum sepenuhnya mencerminkan kualitas pertumbuhan. Tanpa perbaikan efisiensi, pengalaman pelanggan, dan konversi penjual, skala besar justru berisiko menjadi beban sistem dan menurunkan profitabilitas jangka panjang.")
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Metrik Utama")
    total_revenue = payments['payment_value'].sum()
    total_customers = customers['customer_unique_id'].nunique()
    total_orders = orders['order_id'].nunique()
    total_sellers = sellers['seller_id'].nunique()
    total_products = products['product_id'].nunique()
    st.metric(label="Total Pendapatan (R$)", value=f"R$ {total_revenue/1_000_000:,.2f} Jt".replace(",", "X").replace(".", ",").replace("X", "."))
    st.metric(label="Total Pelanggan", value=f"{total_customers:,}".replace(",", "."))
    st.metric(label="Total Pesanan", value=f"{total_orders:,}".replace(",", "."))
    st.metric(label="Total Penjual (Seller)", value=f"{total_sellers:,}".replace(",", "."))
    st.metric(label="Total Produk", value=f"{total_products:,}".replace(",", "."))
with col2:
    st.subheader("Pendapatan Meningkat, Tapi Tanda Perlambatan Mulai Terlihat")
    revenue_over_time = orders.merge(payments, on='order_id')
    revenue_over_time['month'] = revenue_over_time['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
    monthly_revenue = revenue_over_time.groupby('month')['payment_value'].sum().reset_index()
    fig = px.area(monthly_revenue, x='month', y='payment_value', title="Pertumbuhan Pendapatan Seiring Waktu", labels={'month': 'Bulan', 'payment_value': 'Total Pendapatan (R$)'}, color_discrete_sequence=[THEME_COLOR], template=PLOTLY_TEMPLATE)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- 4. Analisis Preferensi Pelanggan ---
st.header("Permintaan Terdistribusi Tidak Merata di Setiap Wilayah")
st.markdown("Data menunjukkan konsentrasi kategori populer berbeda signifikan antar provinsi. Tanpa pendekatan berbasis wilayah dalam pengelolaan inventori dan promosi, ketidaksesuaian antara penawaran dan permintaan lokal akan terus menghambat pertumbuhan penjualan regional secara optimal.")

# Siapkan data yang akan digunakan
df_popular = df_master.dropna(subset=['product_category_name_english', 'customer_state'])

# <-- MODIFIKASI: Menambahkan 'Semua Provinsi' ke dalam daftar dan menjadikannya default -->
provinsi_list = ['Semua Provinsi'] + sorted(df_popular['customer_state'].unique().tolist())
selected_state = st.selectbox("Pilih Wilayah Analisis:", provinsi_list)

# --- Tata letak dengan peta di kiri dan grafik di kanan ---
col1, col2 = st.columns([1, 2])

with col1:
    # Tampilkan peta
    map_title = "Peta Pesanan Nasional" if selected_state == 'Semua Provinsi' else f"Lokasi Provinsi: {selected_state}"
    st.markdown(f"**{map_title}**")
    
    state_order_counts = df_popular['customer_state'].value_counts().reset_index()
    state_order_counts.columns = ['state', 'orders']
    
    geojson_url = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson"
    
    fig_map = px.choropleth(
        state_order_counts,
        geojson=geojson_url,
        locations='state',
        featureidkey='properties.sigla',
        color='orders',
        color_continuous_scale="Blues",
        scope="south america"
    )
    
    # <-- MODIFIKASI: Logika kondisional untuk zoom peta -->
    if selected_state == 'Semua Provinsi':
        # Tampilkan seluruh Brasil
        fig_map.update_geos(fitbounds="geojson", visible=False)
    else:
        # Zoom ke provinsi yang dipilih
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.data[0].locations = [selected_state]

    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    # <-- MODIFIKASI: Logika kondisional untuk data grafik batang -->
    if selected_state == 'Semua Provinsi':
        st.markdown("**Top 10 Kategori Produk (Nasional)**")
        top_cats_data = df_popular['product_category_name_english'].value_counts().head(10).reset_index()
    else:
        st.markdown(f"**Top 10 Kategori Produk di Provinsi {selected_state}**")
        top_cats_data = (
            df_popular[df_popular['customer_state'] == selected_state]
            ['product_category_name_english']
            .value_counts()
            .head(10)
            .reset_index()
        )
    
    top_cats_data.columns = ['Kategori', 'Jumlah Pesanan']
    
    fig_top_cats = px.bar(
        top_cats_data,
        x='Jumlah Pesanan',
        y='Kategori',
        text='Jumlah Pesanan',
        orientation='h',
        color_discrete_sequence=[THEME_COLOR],
        template=PLOTLY_TEMPLATE
    )
    fig_top_cats.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=450,
        yaxis_title="Kategori Produk",
        xaxis_title="Jumlah Pesanan"
    )
    st.plotly_chart(fig_top_cats, use_container_width=True)

st.markdown("---")

# --- 5. Analisis Kualitas Produk & Kepuasan Pelanggan ---
st.header("Inkon­sistensi Kualitas Produk Merusak Persepsi Pelanggan")
st.markdown("Selisih skor ulasan antar kategori mencerminkan ketidakkonsistenan pengalaman pelanggan. Kategori dengan rating rendah perlu dievaluasi secara sistematis karena dapat menurunkan persepsi terhadap keseluruhan platform dan menghambat repeat order di lini produk terkait.")
st.subheader("Peringkat Kategori Produk Berdasarkan Ulasan")
min_reviews = st.slider("Jumlah minimum ulasan untuk ditampilkan:", min_value=10, max_value=200, value=50)
category_quality = df_master.groupby('product_category_name_english').agg(average_score=('review_score', 'mean'), review_count=('review_score', 'count')).reset_index()
category_quality_filtered = category_quality[category_quality['review_count'] >= min_reviews]
col1, col2 = st.columns(2)
with col1:
    st.markdown("##### Kategori dengan Peringkat Tertinggi")
    top_categories = category_quality_filtered.nlargest(5, 'average_score')
    fig_top = px.bar(top_categories, x='average_score', y='product_category_name_english', orientation='h', text=top_categories['average_score'].apply(lambda x: f'{x:.2f}'), color_discrete_sequence=['#2ca02c'], template=PLOTLY_TEMPLATE)
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Skor Rata-rata", yaxis_title=None, xaxis=dict(range=[4,5]))
    st.plotly_chart(fig_top, use_container_width=True)
with col2:
    st.markdown("##### Kategori dengan Peringkat Terendah")
    bottom_categories = category_quality_filtered.nsmallest(5, 'average_score')
    fig_bottom = px.bar(bottom_categories, x='average_score', y='product_category_name_english', orientation='h', text=bottom_categories['average_score'].apply(lambda x: f'{x:.2f}'), color_discrete_sequence=['#d62728'], template=PLOTLY_TEMPLATE)
    fig_bottom.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_title="Skor Rata-rata", yaxis_title=None, xaxis=dict(range=[1,5]))
    st.plotly_chart(fig_bottom, use_container_width=True)

st.subheader("Kualitas Pengiriman Menurukan Kepercayaan")
st.markdown("Ketidakmampuan memenuhi janji pengiriman telah menjadi sumber utama ketidakpuasan pelanggan. Selama titik ini belum diperbaiki, pertumbuhan akuisisi hanya akan diimbangi oleh hilangnya pelanggan lama.")
complaint_keywords = {
    "Late Delivery": ["atras", "demor", "prazo", "lento", "extravia", "nao chegou"],
    "Product Not Received": ["não recebi", "nao recebi", "não entregue", "nao entregue", "nunca chegou", "consta entregue", "caixa vazia"],
    "Missing Items / Partial Delivery": ["falt", "incompleto", "apenas", "só", "parte", "unidade", "kit", "parcial", "quantitade", "somen"],
    "Bad Product Quality / Defective": ["quebra", "defeit", "qualidade ruim", "funciona", "estraga", "avaria", "falso", "caixa", "rasga", "mancha", "costura", "acabamento", "arranha", "amassad", "solto", "velh"],
    "Wrong Item Sent": ["diferente", "erra", "outro", "modelo", "cor ", "trocado", "marca", "tamanho"],
    "Bad Packaging": ["caixa", "embala", "rasgad", "abert", "violad", "frágil", "fragil", "danificad", "pacote"],
    "Bad Service / Seller Issues": ["atendimento", "sem resposta", "ninguem responde", "não resolve", "pós venda", "mau vendedor", "sem retorno", "diálogo", "serviço", "servico"],
    # "Return & Refund Issues": ["devolv", "troca", "dinheiro", "volta", "cancel", "reembolso", "estorno"],
}

def categorize_complaint(comment):
    if not isinstance(comment, str): return "Lainnya"
    comment_lower = comment.lower()
    scores = {category: sum(1 for keyword in keywords if keyword in comment_lower) for category, keywords in complaint_keywords.items()}
    max_score = max(scores.values())
    if max_score == 0: return "Lainnya"
    best_category = [category for category, score in scores.items() if score == max_score][0]
    return best_category

# Siapkan data ulasan negatif
df_neg_reviews = df_master.dropna(subset=['review_comment_message', 'review_comment_message_en', 'review_id'])

# <-- FIX: Hapus duplikat berdasarkan review_id untuk memastikan setiap ulasan unik -->
df_neg_reviews = df_neg_reviews.drop_duplicates(subset=['review_id'])

low_score_reviews = df_neg_reviews[df_neg_reviews['review_score'] <= 2].copy()
low_score_reviews['complaint_category'] = low_score_reviews['review_comment_message'].apply(categorize_complaint)

col1, col2 = st.columns(2)
with col1:
    st.markdown("##### Kategori Keluhan Utama")
    category_counts = low_score_reviews['complaint_category'].value_counts().reset_index()
    fig_complaints = px.bar(category_counts, x='count', y='complaint_category', orientation='h', text_auto=True, color_discrete_sequence=[THEME_COLOR], template=PLOTLY_TEMPLATE)
    fig_complaints.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Jumlah Ulasan Negatif", yaxis_title="Kategori Keluhan")
    st.plotly_chart(fig_complaints, use_container_width=True)
with col2:
    st.markdown("##### Contoh Komentar Ulasan (dalam Bahasa Inggris)")
    if not low_score_reviews.empty:
        complaint_category_list = low_score_reviews['complaint_category'].unique().tolist()
        selected_complaint = st.selectbox("Pilih kategori keluhan untuk melihat contoh:", options=complaint_category_list)
        
        sample_comments = low_score_reviews[low_score_reviews['complaint_category'] == selected_complaint]
        # Tampilkan hingga 50 sampel unik
        st.dataframe(sample_comments[['review_score', 'review_comment_message_en', 'review_comment_message']].head(50))
    else:
        st.info("Tidak ada komentar untuk ditampilkan.")

st.markdown("---")

def load_data():
    """Loads all e-commerce datasets and parses necessary date columns."""
    path = "E-commerce/"
    orders = pd.read_csv(
        path + "orders_dataset.csv", 
        parse_dates=[
            "order_purchase_timestamp", "order_approved_at",
            "order_delivered_carrier_date", "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    )
    order_items = pd.read_csv(path + "order_items_dataset.csv", parse_dates=["shipping_limit_date"])
    products = pd.read_csv(path + "products_dataset.csv")
    cat_trans = pd.read_csv(path + "product_category_name_translation.csv")
    customers = pd.read_csv(path + "customers_dataset.csv")
    
    return orders, order_items, products, cat_trans, customers

# Load all data
orders, order_items, products, cat_trans, customers = load_data()

# --- 2. Initial Data Merging & Preparation ---
items = order_items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
items = items.merge(cat_trans, on="product_category_name", how="left")
# Apply human-readable formatting to category names
items['product_category_name_english'] = items['product_category_name_english'].dropna().apply(format_snake_case)

# --- 3. Page Configuration ---
st.set_page_config(page_title="E-commerce Operational Dashboard", layout="wide")

# --- 4. Sidebar ---
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    st.write("Use the controls on the main page to filter and drill-down into the data.")

# --- 5. Main Dashboard Title ---
st.title("📈 E-commerce Operational Dashboard")

# --- Data Prep for the entire dashboard ---
df_analysis = orders.merge(items, on='order_id', how='left')
df_analysis = df_analysis[df_analysis['order_status'] == 'delivered'].dropna(
    subset=['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date', 'shipping_limit_date', 'product_category_name_english']
)
df_analysis['days_late'] = (df_analysis['order_delivered_customer_date'] - df_analysis['order_estimated_delivery_date']).dt.total_seconds() / (24 * 3600)
df_analysis['is_on_time'] = df_analysis['days_late'] <= 0
df_analysis['seller_dispatched_on_time'] = df_analysis['order_delivered_carrier_date'] <= df_analysis['shipping_limit_date']
df_analysis['seller_dispatch_days_late'] = (df_analysis['order_delivered_carrier_date'] - df_analysis['shipping_limit_date']).dt.total_seconds() / (24 * 3600)
df_analysis = df_analysis.merge(customers[['customer_id', 'customer_state']], on='customer_id', how='left')

# --- 6. High-Level Fulfillment KPIs ---
st.header("🚚 Overall Fulfillment Performance")
st.subheader("🎯 Key Performance Indicators (All Categories)")
col1, col2, col3, col4 = st.columns(4)
late_rate = (~df_analysis['is_on_time']).mean() * 100
col1.metric("Late Delivery Rate", f"{late_rate:.1f}%", help="Persentase pesanan yang diterima pelanggan setelah estimasi tanggal pengiriman (semakin rendah semakin baik).")

seller_late_rate = (~df_analysis['seller_dispatched_on_time']).mean() * 100
col2.metric("Late Seller Dispatch", f"{seller_late_rate:.1f}%", help="Persentase item yang dikirim seller setelah batas waktu pengiriman ke ekspedisi.")

avg_days_late = df_analysis.loc[~df_analysis['is_on_time'], 'days_late'].mean()
col3.metric("Rata-rata Hari Keterlambatan", f"{avg_days_late:.1f} hari", help="Rata-rata keterlambatan pengiriman yang tidak on-time (semakin kecil semakin baik).")

late_orders_count = (~df_analysis['is_on_time']).sum()
col4.metric("Jumlah Delivery Terlambat", f"{late_orders_count:,}", help="Total pesanan yang terlambat dari seluruh pengiriman delivered.")


# --- NEW: OTD and Seller Dispatch Rate Trend Over Time ---
st.subheader("📊 Performance Trend Over Time")
df_analysis['month'] = df_analysis['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
monthly_performance = df_analysis.groupby('month').agg(
    customer_late_rate = ('is_on_time', lambda x: (~x).mean() * 100),
    seller_late_rate = ('seller_dispatched_on_time', lambda x: (~x).mean() * 100)
).reset_index()

# Filter hanya order yang telat (days_late > 0)
late_orders = df_analysis[df_analysis['days_late'] > 0].copy()
late_orders['month'] = late_orders['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()

# Group by bulan
monthly_days_late = late_orders.groupby('month')['days_late'].mean().reset_index()

import plotly.express as px

fig_dayslate_trend = px.line(
    monthly_days_late,
    x='month',
    y='days_late',
    markers=True,
    title="Tren Rata-rata Hari Keterlambatan per Bulan"
)
fig_dayslate_trend.update_layout(
    yaxis_title="Rata-rata Hari Terlambat",
    xaxis_title="Bulan"
)
st.plotly_chart(fig_dayslate_trend, use_container_width=True)
# --- 6.1 KPI Metrics for Total Sellers and Products ---
# Melt the dataframe to plot both lines
monthly_late_melted = monthly_performance.melt(
    id_vars='month',
    value_vars=['customer_late_rate', 'seller_late_rate'],
    var_name='metric_type',
    value_name='rate'
)
rename_map = {
    'customer_late_rate': 'Customer Late Delivery Rate',
    'seller_late_rate': 'Seller Late Dispatch Rate'
}
monthly_late_melted['metric_type'] = monthly_late_melted['metric_type'].map(rename_map)

fig_late_trend = px.line(
    monthly_late_melted,
    x='month', y='rate', color='metric_type',
    title="Tren Late Rate (Pengiriman & Dispatch) Bulanan",
    markers=True
)
fig_late_trend.update_layout(
    yaxis_title="Late Rate (%)", xaxis_title="Bulan", legend_title_text='Metric'
)
st.plotly_chart(fig_late_trend, use_container_width=True)
st.markdown("---")

# --- 7. Interactive Regional and Product Analysis ---
st.header("Wilayah Berkinerja Buruk Menjadi Beban Pertumbuhan")
st.markdown("Provinsi dengan tingkat pengiriman rendah secara langsung menurunkan performa rata-rata nasional. Tanpa prioritas perbaikan di area ini, ekspansi hanya akan menambah volume masalah, bukan nilai bisnis.")

col1, col2 = st.columns(2)
with col1:
    map_metric_selection = st.radio("Select Map Metric:", options=["Customer On-Time Rate", "Seller On-Time Dispatch Rate"], horizontal=True)
with col2:
    category_list = ['All Categories'] + sorted(df_analysis['product_category_name_english'].dropna().unique().tolist())
    selected_category_regional = st.selectbox("Filter by Product Category:", options=category_list)

df_regional = df_analysis.copy()
if selected_category_regional != 'All Categories':
    df_regional = df_regional[df_regional['product_category_name_english'] == selected_category_regional]

st.subheader("Regional Performance Drill-Down")
col1, col2 = st.columns([1, 2])
with col1:
    state_list = ['All States'] + sorted(df_regional['customer_state'].dropna().unique().tolist())
    selected_state = st.selectbox("Select a State to Analyze:", options=state_list)
    
    if map_metric_selection == "Customer On-Time Rate":
        metric_by_state = df_regional.groupby('customer_state')['is_on_time'].mean().mul(100).reset_index(name='metric_value')
        map_title = "Customer OTD Rate (%)"
    else:
        metric_by_state = df_regional.groupby('customer_state')['seller_dispatched_on_time'].mean().mul(100).reset_index(name='metric_value')
        map_title = "Seller Dispatch Rate (%)"
    
    geojson_url = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson"
    fig_regional_map = px.choropleth(metric_by_state, geojson=geojson_url, locations='customer_state', featureidkey='properties.sigla', color='metric_value', color_continuous_scale="RdYlGn", range_color=(70, 100), scope="south america", labels={'metric_value': map_title})
    fig_regional_map.update_geos(fitbounds="locations", visible=False)
    fig_regional_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, title_text=f"{map_title} for {selected_category_regional}")
    st.plotly_chart(fig_regional_map, use_container_width=True)

with col2:
    state_filtered_data = df_regional
    if selected_state != 'All States':
        state_filtered_data = df_regional[df_regional['customer_state'] == selected_state]
    
    category_title = f"for {selected_category_regional} " if selected_category_regional != 'All Categories' else ""
    state_title = f"in {selected_state}" if selected_state != 'All States' else "in All States"

    if map_metric_selection == "Customer On-Time Rate":
        late_data = state_filtered_data[~state_filtered_data['is_on_time']].copy()
        if not late_data.empty:
            # Set bin width 1 hari, range 0 - 16 (atau sesuai distribusi data)
            bins = [0, 3, 6, 9, 12, 15, np.inf]
            labels = ["0-2", "3-5", "6-8", "9-11", "12-14", "15+"]

            late_data['days_late_bin'] = pd.cut(
                late_data['days_late'],
                bins=bins,
                labels=labels,
                right=False,      # bin [start, end)
                include_lowest=True
            )

            # Agregasi
            binned_counts = late_data['days_late_bin'].value_counts().reindex(labels, fill_value=0).reset_index()
            binned_counts.columns = ['days_late_bin', 'count']

            fig_bar = px.bar(
                binned_counts, 
                x='days_late_bin', 
                y='count', 
                text_auto=True,
                title=f"Distribusi Hari Keterlambatan (Interval 3 Hari, '15+' Digabung) {category_title}{state_title}",
                labels={'days_late_bin': 'Rentang Hari Keterlambatan', 'count': 'Jumlah Order Terlambat'}
            )
            fig_bar.update_layout(
                bargap=0.25,
                yaxis_title="Jumlah Order Terlambat",
                xaxis_title="Hari Keterlambatan (Binned)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Tidak ada data keterlambatan pada kriteria ini.")

            
    else: # Seller On-Time Dispatch Rate
        late_data = state_filtered_data[~state_filtered_data['seller_dispatched_on_time']].copy()
        if not late_data.empty:
            bins = list(np.arange(0, 21, 5)) + [np.inf]
            labels = [f"{i} - {i+5}" for i in np.arange(0, 20, 5)] + ["20+"]
            late_data['lateness_bin'] = pd.cut(late_data['seller_dispatch_days_late'], bins=bins, labels=labels, right=False)
            binned_counts = late_data['lateness_bin'].value_counts().sort_index().reset_index()
            binned_counts.columns = ['lateness_bin', 'count']

            fig_dist = px.bar(binned_counts, x='lateness_bin', y='count', text_auto=True, title=f'Distribution of Seller Dispatch Lateness {category_title}{state_title}')
            fig_dist.update_layout(yaxis_title="Count of Late Orders", xaxis_title='Seller Dispatch Days Late (Binned)', xaxis={'categoryorder':'array', 'categoryarray': labels})
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No late seller dispatches to display for the selected criteria.")
st.markdown("---")

# Proses: Jam, agar mudah dibandingkan
df_analysis['order_processing_time'] = (df_analysis['order_approved_at'] - df_analysis['order_purchase_timestamp']).dt.total_seconds() / 3600
df_analysis['seller_lead_time'] = (df_analysis['order_delivered_carrier_date'] - df_analysis['order_approved_at']).dt.total_seconds() / 3600
df_analysis['shipping_time'] = (df_analysis['order_delivered_customer_date'] - df_analysis['order_delivered_carrier_date']).dt.total_seconds() / 3600

df_time_filtered = df_analysis.copy()
if selected_state != 'All States':
    df_time_filtered = df_time_filtered[df_time_filtered['customer_state'] == selected_state]

avg_processing = df_time_filtered['order_processing_time'].mean()
avg_seller_lead = df_time_filtered['seller_lead_time'].mean()
avg_shipping = df_time_filtered['shipping_time'].mean()

labels = ['Order Processing', 'Seller to Carrier', 'Carrier to Customer']
values = [avg_processing, avg_seller_lead, avg_shipping]
percentages = [v / sum(values) * 100 for v in values]

import plotly.graph_objects as go

fig_avg = go.Figure(go.Bar(
    x=labels,
    y=values,
    text=[f"{v:.1f} jam<br>({p:.1f}%)" for v, p in zip(values, percentages)],
    textposition='auto',
    marker_color=['#4e79a7', '#f28e2c', '#e15759']
))

st.subheader("Bottleneck Pengiriman Menghancurkan Pengalaman Pengguna")
st.markdown("Kurir ke pelanggan menyumbang 73% waktu pengiriman. Seberapa cepat proses sebelumnya tidak lagi relevan jika tahap akhir membuat pelanggan kecewa. Satu kesalahan di sini bisa menghapus seluruh upaya membangun kepuasan.")
fig_avg.update_layout(
    title=f"Rata-rata Breakdown Waktu Pengiriman ({selected_state})",
    yaxis_title="Rata-rata Waktu (jam)",
    xaxis_title="Proses"
)
st.plotly_chart(fig_avg, use_container_width=True)

# --- 6. Analisis Potensi Perluasan Pasar ---
st.markdown("---")
counts = deals['lead_type'].value_counts().sort_values()
proportions = counts / counts.sum()
fig_leads = px.bar(x=proportions.values, y=proportions.index, orientation='h', labels={'x': 'Persentase Prospek', 'y': 'Tipe Prospek'}, title='Distribusi Tipe Prospek Penjual yang Berhasil Diakuisisi', color_discrete_sequence=[THEME_COLOR], template=PLOTLY_TEMPLATE)
fig_leads.update_traces(text=[f'{p:.1%}' for p in proportions.values], textposition='auto')
fig_leads.update_layout(xaxis_tickformat='.1%')
col1, col2 = st.columns([2, 1])
with col1:
    st.plotly_chart(fig_leads, use_container_width=True)
with col2:
    pct = proportions.get('Online Medium', 0) # Pastikan nama lead_type sesuai
    pct_str = f'{pct:.1%}'.replace('.', ',')
    st.subheader('Penjual "Online Medium" sebagai Kunci Pertumbuhan')
    st.write(f"Dengan **39% penjual** yang berhasil diakuisisi berada di segmen 'Online Medium', strategi pemasaran harus fokus pada aktivasi & akselerasi mereka. Insentif yang tepat dan kampanye pertumbuhan dapat membuka potensi pendapatan yang signifikan dari segmen ini.")

# ===============================
df = pd.merge(deals, leads[['mql_id', 'first_contact_date', 'origin']], on='mql_id', how='left')

# Hitung durasi konversi (dalam hari)
df['conversion_days'] = (df['won_date'] - df['first_contact_date']).dt.days

# Hitung rata-rata durasi per origin
avg_conversion = df.groupby('origin')['conversion_days'].mean().sort_values(ascending=False).reset_index()

# Visualisasi
fig = px.bar(
    avg_conversion,
    x='conversion_days', y='origin',
    orientation='h',
    color='conversion_days',
    color_continuous_scale='blues',
    labels={'conversion_days': 'Rata-rata Hari Konversi', 'origin': 'Channel (Origin)'},
    title='⏱️ Rata-rata Waktu Konversi Lead Menjadi Seller per Channel (Origin)',
    template=PLOTLY_TEMPLATE
)

fig.update_traces(text=avg_conversion['conversion_days'].round(1), textposition='outside')
fig.update_layout(coloraxis_showscale=False)

# Tampilkan chart
st.plotly_chart(fig, use_container_width=True)

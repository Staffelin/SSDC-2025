import streamlit as st
import pandas as pd
import plotly.express as px

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

    except FileNotFoundError as e:
        st.error(f"Error: Salah satu file dataset tidak ditemukan di '{path}'. Pastikan semua file ada, termasuk 'order_reviews_dataset_translated.csv'.")
        st.stop()
    return payments, customers, orders, sellers, products, order_items, reviews, cat_trans, deals

def format_snake_case(s):
    if isinstance(s, str): return s.replace('_', ' ').title()
    return s

# Memuat semua data
payments, customers, orders, sellers, products, order_items, reviews, cat_trans, deals = load_data()

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
st.header("Gambaran Umum Kinerja Operasional")
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
    st.subheader("Tren Pendapatan Bulanan")
    revenue_over_time = orders.merge(payments, on='order_id')
    revenue_over_time['month'] = revenue_over_time['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
    monthly_revenue = revenue_over_time.groupby('month')['payment_value'].sum().reset_index()
    fig = px.area(monthly_revenue, x='month', y='payment_value', title="Pertumbuhan Pendapatan Seiring Waktu", labels={'month': 'Bulan', 'payment_value': 'Total Pendapatan (R$)'}, color_discrete_sequence=[THEME_COLOR], template=PLOTLY_TEMPLATE)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- 4. Analisis Preferensi Pelanggan ---
st.header("📊 Analisis Preferensi Pelanggan")
st.markdown("Pilih sebuah provinsi untuk melihat kategori produk yang paling diminati di wilayah tersebut, atau pilih 'Semua Provinsi' untuk melihat gambaran nasional.")

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
st.header("💬 Umpan Balik & Kualitas Produk")
st.markdown("Menganalisis ulasan pelanggan untuk menemukan titik kekuatan dan area yang memerlukan perbaikan.")
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

st.markdown("---")

# --- Analisis Ulasan Negatif ---
st.subheader("Analisis Ulasan Negatif (Skor ≤ 2)")

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

# --- 6. Analisis Potensi Perluasan Pasar ---
st.header("🚀 Potensi Perluasan Pasar (Analisis Prospek Penjual)")
st.markdown("Menganalisis data prospek penjual (leads) untuk mengidentifikasi peluang pertumbuhan di segmen B2B atau penjual profesional.")
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
    st.write(f"Dengan **{pct_str}** penjual yang berhasil diakuisisi berada di segmen 'Online Medium', strategi pemasaran harus fokus pada aktivasi & akselerasi mereka. Insentif yang tepat dan kampanye pertumbuhan dapat membuka potensi pendapatan yang signifikan dari segmen ini.")
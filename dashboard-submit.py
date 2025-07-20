import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Analisis Kinerja E-commerce",
    layout="wide"
)

THEME_COLOR = "royalblue"
PLOTLY_TEMPLATE = "plotly_white"

@st.cache_data
def load_data():
    path = "E-commerce/"
    try:
        payments = pd.read_csv("https://drive.google.com/uc?id=113dmpJdb8hA8urg45nYkYXDWhdFvCBYL")
        customers = pd.read_csv("https://drive.google.com/uc?id=1F2-guLBn-XsTf9TKg6lMrFYHZR_CZbpl")
        orders = pd.read_csv("https://drive.google.com/uc?id=11CtVRGgAEmKYPFYmcDwbVLgpZg_smDfo", parse_dates=['order_purchase_timestamp', 'order_delivered_customer_date', 'order_estimated_delivery_date', 'order_approved_at', 'order_delivered_carrier_date'])
        sellers = pd.read_csv("https://drive.google.com/uc?id=1hWy1kOf2X6dr2gaP5DuanPqyjNdYuxui")
        products = pd.read_csv("https://drive.google.com/uc?id=14BWKVgA4HuRRat8BJxkYIJA6A0pcw0Kr")
        order_items = pd.read_csv("https://drive.google.com/uc?id=1dtiJfdrUDZoduKu-y29j_BSoi4uwwcAE", parse_dates=["shipping_limit_date"])
        deals = pd.read_csv("https://drive.google.com/uc?id=1Y-nwkv9D91luGetDrVanJQpPrPLyQnY9", parse_dates=["won_date"])
        cat_trans = pd.read_csv("https://drive.google.com/uc?id=1gLiDRqex2oFmE62t2hMXlRJUxv6kjLZ5")
        reviews = pd.read_csv("https://drive.google.com/uc?id=1JAge-xr3SkoTI-_wPpW7gHQaanZ-DWMF")
        leads = pd.read_csv("https://drive.google.com/uc?id=1Ec2sgXZG4JMWlcHzg5NbDUrXw6okdSBa", parse_dates=["first_contact_date"])

    except FileNotFoundError as e:
        missing_file = str(e).split("'")[1] if "'" in str(e) else str(e)
        st.error(f"Error: File dataset '{missing_file}' tidak ditemukan di '{path}'. Pastikan semua file ada.")
        st.stop()
    return payments, customers, orders, sellers, products, order_items, reviews, cat_trans, deals, leads

def format_snake_case(s):
    if isinstance(s, str): return s.replace('_', ' ').title()
    return s

payments, customers, orders, sellers, products, order_items, reviews, cat_trans, deals, leads = load_data()

items = order_items.merge(products, on="product_id", how="left")
items = items.merge(cat_trans, on="product_category_name", how="left")
items['product_category_name_english'] = items['product_category_name_english'].apply(format_snake_case)
df_master = orders.merge(reviews, on="order_id", how="left")
df_master = df_master.merge(items, on="order_id", how="left")
df_master = df_master.merge(customers, on='customer_id', how='left')
df_master['product_category_name_english'] = df_master['product_category_name_english'].dropna().apply(format_snake_case)

st.title("Scalability Through Continuity")
st.markdown("Made by Astutea - SSDC2025006")
st.markdown(" E-Commerce telah mencapai skala yang besar dalam waktu yang pesat, dengan hampir 100.000 pesanan dan 96.000 pelanggan dalam 2 tahun. Namun, pertumbuhan pendapatan menunjukkan **tanda-tanda stagnasi** dan perusahaan masih memiliki banyak **permasalahan dalam segi kualitas pengiriman, relevansi produk, serta kerataan penjual**. *Dashboard* ini mengungkap area strategis yang harus diperbaiki untuk mendorong pertumbuhan berkelanjutan. Fokus pembahasan diarahkan pada **memahami preferensi pelanggan dan inventori, optimasi logistik, dan pertumbuhan pasar yang akurat**. Diharapkan agar strategi yang diusulkan pada *dashboard* ini dapat menjadi perintis dalam memutarkan kembali roda pertumbuhan perusahaan.")
st.markdown("---")

st.header("Perusahaan Sudah Berkembang Pesat, Akankah Terus Seperti Ini?")
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Statistik Terlihat Bagus, Namun...")
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
    st.subheader("Pendapatan Sudah Mulai Stagnan")
    revenue_over_time = orders.merge(payments, on='order_id')
    revenue_over_time['month'] = revenue_over_time['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
    monthly_revenue = revenue_over_time.groupby('month')['payment_value'].sum().reset_index()
    fig = px.area(monthly_revenue, x='month', y='payment_value', title="Sudah 9 Bulan Tanpa Rekor Baru Pendapatan (Terakhir Nov 2017)", labels={'month': 'Bulan', 'payment_value': 'Total Pendapatan (R$)'}, color_discrete_sequence=[THEME_COLOR], template=PLOTLY_TEMPLATE)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
st.markdown("Hampir 100.000 pesanan dan 96.000 pelanggan mencerminkan bahwa perusahaan ini memiliki skala operasional yang luas. **Namun**, kondisi ini belum sepenuhnya mencerminkan kualitas pertumbuhan. Tanpa **perbaikan** dalam segi **pengalaman pengguna**, **efisiensi**, dan **konversi penjual**, skala besar justru berisiko menjadi **beban perusahaan** dan menurunkan **profitabilitas jangka panjang perusahaan**.")

st.markdown("---")

st.header("Bagaimana Kondisi Perusahaan Saat Ini?")
st.markdown("Agar mengetahui langkah yang dapat diambil agar perusahaan tetap tumbuh, perlu diketahui terlebih dahulu kondisi *e-commerce* saat ini, seperti **analisis pengalaman pengguna** serta **efisiensi operasional perusahaan**.")

st.markdown("---")

st.header("Apa yang Pelanggan Katakan Tentang Produk Kita?")
st.markdown("*Rating* yang diberikan oleh pelanggan dapat dipengaruhi oleh berbagai **faktor negatif**, seperti **keterlambatan**, **barang yang tidak sampai**, ataupun **cacat produk**. Faktor ini dapat **menurunkan kepercayaan pelanggan** terhadap platform secara keseluruhan dan **mengurangi repeat order** pada kategori yang sama.")
st.subheader("Apa Kategori Produk yang Paling Disukai/Tidak Disukai Pelanggan?")
min_reviews = st.slider("Jumlah minimum ulasan untuk ditampilkan:", min_value=10, max_value=200, value=50)
category_quality = df_master.groupby('product_category_name_english').agg(average_score=('review_score', 'mean'), review_count=('review_score', 'count')).reset_index()
category_quality_filtered = category_quality[category_quality['review_count'] >= min_reviews]
col1, col2 = st.columns(2)
with col1:
    st.markdown("##### Kategori dengan Peringkat Tertinggi (Skala 1-5)")
    top_categories = category_quality_filtered.nlargest(5, 'average_score')
    fig_top = px.bar(top_categories, x='average_score', y='product_category_name_english', orientation='h', text=top_categories['average_score'].apply(lambda x: f'{x:.2f}'), color_discrete_sequence=['#2ca02c'], template=PLOTLY_TEMPLATE)
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Skor Rata-rata", yaxis_title=None, xaxis=dict(range=[1,5]))
    st.plotly_chart(fig_top, use_container_width=True)
with col2:
    st.markdown("##### Kategori dengan Peringkat Terendah (Skala 1-5)")
    bottom_categories = category_quality_filtered.nsmallest(5, 'average_score')
    fig_bottom = px.bar(bottom_categories, x='average_score', y='product_category_name_english', orientation='h', text=bottom_categories['average_score'].apply(lambda x: f'{x:.2f}'), color_discrete_sequence=['#d62728'], template=PLOTLY_TEMPLATE)
    fig_bottom.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_title="Skor Rata-rata", yaxis_title=None, xaxis=dict(range=[1,5]))
    st.plotly_chart(fig_bottom, use_container_width=True)

st.markdown("Terlihat kategori-kategori yang memiliki nilai ulasan tertinggi dan terendah. **Lantas mengapa** kategori tersebut memiliki nilai ulasan yang rendah?")

st.subheader("Rendahnya Kualitas Pengiriman Menurunkan Kepercayaan Pelanggan")

complaint_keywords = {
    "Late Delivery": ["atras", "demor", "prazo", "lento", "extravia", "pass"],
    "Missing Items / Partial Delivery": ["falt", "incompleto", "apenas", "só", " so ", "parte", "unidade", "kit", "parcial", "quantitade", "somen"],
    "Product Not Received": ["nao chegou", "não chegou", "não rece", "nao rece", "não entreg", "nao entreg", "nunca chegou", "consta entregue", "caixa vazia", "aguard", "nada", "nao foi entreg", "não foi entreg"],
    "Bad Product Quality / Defective": ["peq", "quebra", "defeit", "qualidade ruim", "funciona", "estraga", "avaria", "falso", "caixa", "rasga", "mancha", "costura", "acabamento", "arranha", "amassad", "solto", "velh", "fraco", "materi", "fals"],
    "Wrong Item Sent": ["diferente", "erra", "outro", "modelo", "cor ", "trocado", "marca", "tamanho", "correspondem", "nao foi o mesm", "não foi o mesm"],
    "Bad Packaging": ["caixa", "embala", "rasgad", "abert", "violad", "frágil", "fragil", "danificad", "pacote"],
    "Bad Service / Seller Issues": ["atendimen", "sem resp", "ninguem resp", "nao resol", "não resolve", "pós venda", "vendedor", "dialo", "diálo", "serviç", "servic", "respe", "loj"],
    "Misleading Product / Advertisement": ["propagan", "anunc", "fot", "descri", "expect", "ilus", "nao e como", "não é como", "origin"],
    # "Return & Refund Issues": ["devolv", "troca", "dinheiro", "volta", "cancel", "reembolso", "estorno"],
    "Return / Refund / Cancellation Issues": ["cancel", "devol", "troca"]
}

def categorize_complaint(comment):
    if not isinstance(comment, str): return "Unclassified"
    comment_lower = comment.lower()
    scores = {category: sum(1 for keyword in keywords if keyword in comment_lower) for category, keywords in complaint_keywords.items()}
    max_score = max(scores.values())
    if max_score == 0: return "Unclassified"
    best_category = [category for category, score in scores.items() if score == max_score][0]
    return best_category

df_neg_reviews = df_master.dropna(subset=['review_comment_message', 'review_comment_message_en', 'review_id'])
df_neg_reviews = df_neg_reviews.drop_duplicates(subset=['review_id'])
low_score_reviews_all = df_neg_reviews[df_neg_reviews['review_score'] <= 2].copy()
low_score_reviews_all['complaint_category'] = low_score_reviews_all['review_comment_message'].apply(categorize_complaint)

category_filter_list = ['Semua Kategori'] + sorted(df_neg_reviews['product_category_name_english'].dropna().unique().tolist())
selected_prod_category = st.selectbox(
    "Pilih Kategori Produk untuk dianalisis:",
    options=category_filter_list
)

if selected_prod_category != 'Semua Kategori':
    low_score_reviews = low_score_reviews_all[low_score_reviews_all['product_category_name_english'] == selected_prod_category]
else:
    low_score_reviews = low_score_reviews_all

col1, col2 = st.columns(2)
with col1:
    st.markdown("##### Keluhan Paling Umum dari Ulasan Negatif (<= 2 Bintang)")
    if not low_score_reviews.empty:
        category_counts = low_score_reviews['complaint_category'].value_counts().reset_index()
        
        total_negative_reviews = category_counts['count'].sum()
        category_counts['percentage'] = (category_counts['count'] / total_negative_reviews) * 100
        category_counts['text_label'] = category_counts.apply(
            lambda row: f"{row['count']:,} ({row['percentage']:.1f}%)".replace(",", "."), axis=1
        )

        fig_complaints = px.bar(
            category_counts, 
            x='count', 
            y='complaint_category', 
            orientation='h',
            text='text_label',
            color_discrete_sequence=[THEME_COLOR], 
            template=PLOTLY_TEMPLATE
        )
        fig_complaints.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            xaxis_title="Jumlah Ulasan Negatif", 
            yaxis_title="Kategori Keluhan"
        )
        st.plotly_chart(fig_complaints, use_container_width=True)
    else:
        st.info("Tidak ada ulasan negatif untuk kategori yang dipilih.")
with col2:
    st.markdown("##### Contoh Komentar Ulasan (Ditranslasi ke Bahasa Inggris)")
    if not low_score_reviews.empty:
        complaint_category_list = low_score_reviews['complaint_category'].unique().tolist()
        selected_complaint = st.selectbox("Pilih kategori keluhan untuk melihat contoh:", options=complaint_category_list)
        
        sample_comments = low_score_reviews[low_score_reviews['complaint_category'] == selected_complaint]
        st.dataframe(sample_comments[['review_score', 'review_comment_message_en']].head(50))
    else:
        st.info("Tidak ada komentar untuk ditampilkan.")
st.caption("**Disclaimer**: Ulasan ini dikategorikan secara otomatis dengan mencari kata kunci tertentu dalam komentar. Kesalahan klasifikasi mungkin terjadi.")

st.markdown("Ketidakpastian atas pengiriman produk, seperti **pengiriman yang tidak tepat waktu**, **barang tidak lengkap**, bahkan **barang yang sama sekali tidak sampai pengirim** merupakan faktor utama penyebab ulasan rendah. Hal yang sama berlaku untuk beberapa kategori produk dengan ulasan rendah (Office Furniture, Fixed Telephony).")
st.markdown("Kategori produk lain memiliki keluhan yang lebih **spesifik terhadap kategorinya**, misalnya Fashion Male Clothing yang memiliki banyak masalah tentang **salah pengiriman** dan **refund** (contohnya masalah ukuran yang tidak cocok).")

st.markdown("""
Berdasarkan keluhan yang paling sering dialami, rekomendasi yang kami dapat berikan adalah penerapan **Service Level Agreement (SLA)**. SLA adalah kontrak antara penyedia dan pelanggan untuk mendefinisikan standar pelayanan yang dapat diekspektasikan pelanggan kepada penyedia. SLA berfungsi untuk memberikan jaminan bahwa tidak ada produk yang **telat diantar/tidak diterima**. Ini dilakukan dengan mendefinisikan **deadline** yang jelas untuk pengiriman, memberi **sanksi** kepada penyedia jika gagal memenuhi kontrak, serta memberikan **reimbursement** kepada pelanggan.
""")

st.markdown("---")

def load_data():
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


# orders, order_items, products, cat_trans, customers = load_data()

items = order_items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
items = items.merge(cat_trans, on="product_category_name", how="left")

items['product_category_name_english'] = items['product_category_name_english'].dropna().apply(format_snake_case)

df_analysis = orders.merge(items, on="order_id", how="left")
df_analysis = df_analysis[df_analysis['order_status'] == 'delivered'].dropna(
    subset=[
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date',
        'shipping_limit_date',
        'product_category_name_english'
    ]
)
df_analysis['days_late'] = (
    df_analysis['order_delivered_customer_date'] - df_analysis['order_estimated_delivery_date']
).dt.total_seconds() / (24 * 3600)
df_analysis['is_on_time'] = df_analysis['days_late'] <= 0
df_analysis['seller_dispatched_on_time'] = (
    df_analysis['order_delivered_carrier_date'] <= df_analysis['shipping_limit_date']
)
df_analysis['seller_dispatch_days_late'] = (
    df_analysis['order_delivered_carrier_date'] - df_analysis['shipping_limit_date']
).dt.total_seconds() / (24 * 3600)
df_analysis = df_analysis.merge(customers[['customer_id', 'customer_state']], on='customer_id', how='left')

st.header("Masih Banyak yang Perlu Diperbaiki dari Sistem Pengiriman Kita")

late_rate = (~df_analysis['is_on_time']).mean() * 100
seller_late_rate = (~df_analysis['seller_dispatched_on_time']).mean() * 100
avg_days_late = df_analysis.loc[~df_analysis['is_on_time'], 'days_late'].mean()
late_orders_count = (~df_analysis['is_on_time']).sum()

df_analysis['month'] = df_analysis['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
monthly_performance = df_analysis.groupby('month').agg(
    customer_late_rate=('is_on_time', lambda x: (~x).mean() * 100),
    seller_late_rate=('seller_dispatched_on_time', lambda x: (~x).mean() * 100)
).reset_index()

late_orders = df_analysis[df_analysis['days_late'] > 0].copy()
late_orders['month'] = late_orders['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()

monthly_days_late = late_orders.groupby('month')['days_late'].mean().reset_index()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Angka Keterlambatan Masih Tinggi...")
    st.metric("Late Delivery Rate", f"{late_rate:.1f}%", help="Persentase pesanan yang diterima pelanggan setelah estimasi tanggal pengiriman.")
    st.metric("Late Seller Dispatch", f"{seller_late_rate:.1f}%", help="Persentase item yang dikirim seller setelah batas waktu.")
    st.metric("Rata-rata Hari Keterlambatan", f"{avg_days_late:.1f} hari", help="Rata-rata keterlambatan pengiriman yang tidak on-time.")
    st.metric("Jumlah Pengiriman Terlambat", f"{late_orders_count:,}".replace(",", "."), help="Total pesanan yang terlambat dari seluruh pengiriman.")

with col2:
    st.subheader("Dan Semakin Tidak Stabil Seiring Waktu")
    
    if 'month' not in df_analysis.columns:
        df_analysis['month'] = df_analysis['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
        
    monthly_customer_late_rate = df_analysis.groupby('month').agg(
        customer_late_rate=('is_on_time', lambda x: (~x).mean() * 100)
    ).reset_index()

    fig_performance_trend = px.line(
        monthly_customer_late_rate,
        x='month',
        y='customer_late_rate',
        markers=True,
        title="Tren Tingkat Keterlambatan Pengiriman ke Pelanggan"
    )
    fig_performance_trend.update_layout(
        yaxis_title="Tingkat Keterlambatan (%)",
        xaxis_title="Bulan",
        yaxis=dict(range=[0, 30])
    )
    st.plotly_chart(fig_performance_trend, use_container_width=True)

st.markdown("Terdapat **8.568 pengiriman terlambat** dalam rentang waktu **dua tahun**. Artinya terdapat **3657 pengiriman yang terlambat setiap bulan**.")

st.markdown("---")

st.header("Masalah Keterlambatan Terdiri dari Beberapa Aspek")
st.markdown("Terdapat ketidakmerataan angka keterlambatan di beberapa provinsi. Selain itu, distribusi lama keterlambatan juga memberikan pola unik.")

control_col1, control_col2, control_col3 = st.columns(3)

with control_col1:
    map_metric_selection = st.radio(
        "Pilih Metrik Peta:",
        options=["Customer Lateness Rate", "Seller Late Dispatch Rate"],
        horizontal=True,
        key="map_metric_selector"
    )

with control_col3:
    category_list = ['Semua Kategori'] + sorted(df_analysis['product_category_name_english'].dropna().unique().tolist())
    selected_category_regional = st.selectbox(
        "Pilih Kategori Produk:",
        options=category_list,
        key="category_selector"
    )

df_regional = df_analysis.copy()
if selected_category_regional != 'Semua Kategori':
    df_regional = df_regional[df_regional['product_category_name_english'] == selected_category_regional]

with control_col2:
    state_list = ['Semua State'] + sorted(df_regional['customer_state'].dropna().unique().tolist())
    selected_state = st.selectbox(
        "Pilih Provinsi:",
        options=state_list,
        key="state_selector"
    )

main_col1, main_col2 = st.columns([1, 2])

with main_col1:
    map_title_prefix = "Customer Lateness Rate" if map_metric_selection == "Customer Lateness Rate" else "Seller Late Dispatch Rate"
    st.subheader(f"{map_title_prefix} (%) per Provinsi")
    
    if map_metric_selection == "Customer Lateness Rate":
        metric_by_state = df_regional.groupby('customer_state')['is_on_time'].apply(lambda x: (~x).mean() * 100).reset_index(name='metric_value')
        map_title = "Customer Lateness Rate (%)"
    else:
        metric_by_state = df_regional.groupby('customer_state')['seller_dispatched_on_time'].apply(lambda x: (~x).mean() * 100).reset_index(name='metric_value')
        map_title = "Seller Late Dispatch Rate (%)"
    
    geojson_url = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson"
    fig_regional_map = px.choropleth(
        metric_by_state, 
        geojson=geojson_url, 
        locations='customer_state', 
        featureidkey='properties.sigla', 
        color='metric_value', 
        color_continuous_scale="RdYlGn_r", 
        range_color=(0, 30),
        scope="south america", 
        labels={'metric_value': map_title}
    )
    fig_regional_map.update_geos(fitbounds="locations", visible=False)
    fig_regional_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_regional_map, use_container_width=True)

with main_col2:
    state_filtered_data = df_regional
    if selected_state != 'Semua State':
        state_filtered_data = df_regional[df_regional['customer_state'] == selected_state]
    
    category_title = f"untuk {selected_category_regional} " if selected_category_regional != 'Semua Kategori' else ""
    state_title = f"di {selected_state}" if selected_state != 'Semua State' else "di Semua Provinsi"

    if map_metric_selection == "Customer Lateness Rate":
        st.subheader("Lama Keterlambatan Pengiriman ke Pembeli")
        late_data = state_filtered_data[~state_filtered_data['is_on_time']].copy()
        if not late_data.empty:
            bins = list(np.arange(0, 16, 3)) + [np.inf]
            labels = [f"{i}-{i+3}" for i in np.arange(0, 15, 3)] + ["15+"]
            late_data['lateness_bin'] = pd.cut(late_data['days_late'], bins=bins, labels=labels, right=False)
            binned_counts = late_data['lateness_bin'].value_counts().sort_index().reset_index()
            binned_counts.columns = ['lateness_bin', 'count']

            total_late = binned_counts['count'].sum()
            binned_counts['percentage'] = (binned_counts['count'] / total_late) * 100
            binned_counts['text_label'] = binned_counts.apply(lambda row: f"{row['count']:,} ({row['percentage']:.1f}%)".replace(",", "."), axis=1)

            fig_dist = px.bar(binned_counts, x='lateness_bin', y='count', text='text_label', title=f'Distribusi Keterlambatan Pelanggan {category_title}{state_title}')
            fig_dist.update_layout(yaxis_title="Jumlah Pesanan Terlambat", xaxis_title='Rentang Hari Keterlambatan')
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Tidak ada data keterlambatan pelanggan pada kriteria ini.")
    else:
        st.subheader("Lama Keterlambatan Pengiriman ke Kurir")
        late_data = state_filtered_data[~state_filtered_data['seller_dispatched_on_time']].copy()
        if not late_data.empty:
            bins = list(np.arange(0, 16, 3)) + [np.inf]
            labels = [f"{i}-{i+3}" for i in np.arange(0, 15, 3)] + ["15+"]
            late_data['lateness_bin'] = pd.cut(late_data['seller_dispatch_days_late'], bins=bins, labels=labels, right=False)
            binned_counts = late_data['lateness_bin'].value_counts().sort_index().reset_index()
            binned_counts.columns = ['lateness_bin', 'count']

            total_late = binned_counts['count'].sum()
            binned_counts['percentage'] = (binned_counts['count'] / total_late) * 100
            binned_counts['text_label'] = binned_counts.apply(lambda row: f"{row['count']:,} ({row['percentage']:.1f}%)".replace(",", "."), axis=1)

            fig_dist = px.bar(binned_counts, x='lateness_bin', y='count', text='text_label', title=f'Distribusi Keterlambatan Penjual {category_title}{state_title}')
            fig_dist.update_layout(yaxis_title="Jumlah Pesanan Terlambat", xaxis_title='Rentang Hari Keterlambatan Penjual', xaxis={'categoryorder':'array', 'categoryarray': labels})
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Tidak ada data keterlambatan penjual pada kriteria ini.")

st.markdown("Provinsi dengan tingkat pengiriman rendah secara langsung menurunkan performa rata-rata nasional. Perbaikan di area seperti ini perlu dilakukan.")
st.markdown("Sangat mungkin juga bahwa keterlambatan yang terjadi merupakan keterlambatan yang sangat drastis, seperti keterlambatan lebih dari 15 hari.")

df_analysis['order_processing_time'] = (df_analysis['order_approved_at'] - df_analysis['order_purchase_timestamp']).dt.total_seconds() / 3600
df_analysis['seller_lead_time'] = (df_analysis['order_delivered_carrier_date'] - df_analysis['order_approved_at']).dt.total_seconds() / 3600
df_analysis['shipping_time'] = (df_analysis['order_delivered_customer_date'] - df_analysis['order_delivered_carrier_date']).dt.total_seconds() / 3600

df_time_filtered = df_analysis.copy()
if selected_state != 'Semua State':
    df_time_filtered = df_time_filtered[df_time_filtered['customer_state'] == selected_state]

avg_processing = df_time_filtered['order_processing_time'].mean()
avg_seller_lead = df_time_filtered['seller_lead_time'].mean()
avg_shipping = df_time_filtered['shipping_time'].mean()

labels = ['Order Processing', 'Seller to Carrier', 'Carrier to Customer']
values = [avg_processing, avg_seller_lead, avg_shipping]
percentages = [v / sum(values) * 100 for v in values]

fig_avg = go.Figure(go.Bar(
    x=labels,
    y=values,
    text=[f"{v:.1f} jam<br>({p:.1f}%)" for v, p in zip(values, percentages)],
    textposition='auto',
    marker_color=['#4e79a7', '#f28e2c', '#e15759']
))

st.subheader("Bottleneck Pengiriman Menghancurkan Pengalaman Pengguna")
st.markdown("Kurir ke pelanggan menyumbang 73% waktu pengiriman. Seberapa cepat proses sebelumnya tidak akan berpengaruh jika pada akhirnya produk akan telat.")
fig_avg.update_layout(
    title=f"Rata-rata Breakdown Waktu Pengiriman ({selected_state})",
    yaxis_title="Rata-rata Waktu (jam)",
    xaxis_title="Proses"
)
st.plotly_chart(fig_avg, use_container_width=True)

st.markdown("Untuk mengatasi masalah **ketidakmerataan keterlambatan secara regional**, strategi yang kami usulkan adalah bekerja sama dengan **mitra regional** serta memberikan **insentif** untuk kurir yang ingin mengantar ke daerah tersebut.")

st.markdown("Untuk mengatasi masalah **keterlambatan sebanyak 15+ hari**, strategi yang kami usulkan mirip dengan sebelumnya, yaitu menggunakan **SLA** untuk **meningkatkan jaminan tepat waktu**.")

st.markdown("Untuk mengatasi masalah waktu pengiriman **Carrier to Customer** yang lama, strategi yang kami usulkan adalah **penetapan SLA, penambahan *sorting hub* di setiap *state*, serta diversifikasi opsi kurir**.")

st.header("Secara Diam-diam, Mahalnya Ongkir Membuat Pelanggan Tidak Senang")
st.markdown("Ternyata, biaya pengiriman pada platform ini sangat tinggi dan berdampak negatif terhadap nilai ulasan pelanggan.")

df_freight_analysis = df_master.dropna(subset=['freight_value', 'price', 'review_score', 'product_category_name_english'])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Median Rasio Ongkos Kirim Terhadap Harga Produk")
    
    median_freight_value = df_freight_analysis['freight_value'].median()
    median_price_value = df_freight_analysis['price'].median()
    
    if median_price_value > 0:
        median_freight_percentage = (median_freight_value / median_price_value) * 100
    else:
        median_freight_percentage = 0
    value_str = f"{median_freight_percentage:.2f}%"
    
    st.markdown(f"""
    <div style="text-align: center; padding-top: 20px;">
        <p style="font-size: 64px; font-weight: bold;">{value_str}</p>
    </div>
    """, unsafe_allow_html=True)
    
with col2:
    st.subheader("Skor Ulasan Rata-rata Menurun saat Ongkir Naik")
    
    bins = [0, 10, 20, 30, 45, float('inf')]
    labels = ["0-10", "10-20", "20-30", "30-45", "45+"]
    df_freight_analysis['freight_bin'] = pd.cut(df_freight_analysis['freight_value'], bins=bins, labels=labels, right=False)
    
    review_by_freight = df_freight_analysis.groupby('freight_bin')['review_score'].mean().reset_index().dropna()
    fig_review_freight = px.bar(
        review_by_freight, 
        x='freight_bin', 
        y='review_score',
        text=review_by_freight['review_score'].round(2),
        title="Pengaruh Ongkos Kirim terhadap Skor Ulasan",
        labels={'freight_bin': 'Kelompok Ongkos Kirim (R$)', 'review_score': 'Skor Ulasan Rata-rata'},
        color_discrete_sequence=['#d62728'],
        template=PLOTLY_TEMPLATE
    )
    fig_review_freight.update_layout(yaxis=dict(range=[3.5, 5]))
    st.plotly_chart(fig_review_freight, use_container_width=True)

st.markdown("Untuk mengatasi masalah ini, strategi yang kami usulkan adalah **memberikan promosi** untuk pesanan dengan harga ongkir tinggi serta **negosiasi biaya** dengan kurir untuk menekan biaya.")

st.markdown("---")

st.header("Apa yang Dapat Kita Lakukan untuk Memperluas Pasar Kita?")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Kategori Produk Berdasarkan Jumlah Pesanan")
    
    df_popular = df_master.dropna(subset=['product_category_name_english'])
    top_cats_data = df_popular['product_category_name_english'].value_counts().head(10).reset_index()
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

with col2:
    st.subheader("Top 10 Segmen Bisnis Penjual")

    deals_with_state = deals.merge(
        sellers[['seller_id', 'seller_state']], on='seller_id', how='left'
    )
    
    deals_with_state['business_segment_formatted'] = deals_with_state['business_segment'].dropna().apply(format_snake_case)
    
    top_segments = (
        deals_with_state['business_segment_formatted']
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_segments.columns = ['Business Segment', 'Jumlah Seller']
    
    fig_top_segments = px.bar(
        top_segments,
        x='Jumlah Seller',
        y='Business Segment',
        text='Jumlah Seller',
        orientation='h',
        color_discrete_sequence=[THEME_COLOR],
        template=PLOTLY_TEMPLATE
    )
    fig_top_segments.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=450,
        yaxis_title="Segmen Bisnis",
        xaxis_title="Jumlah Seller Terakuisisi"
    )
    st.plotly_chart(fig_top_segments, use_container_width=True)

st.subheader("Kesempatan dalam Kesenjangan")
st.markdown("Grafik di atas menunjukkan **kita 10 kategori produk yang paling sering dipesan serta 10 segmen bisnis penjual yang terpopuler**. Dapat dilihat bahwa beberapa kategori produk memiliki **jumlah pesanan yang sangat besar**, namun **tidak ada segmen bisnis** yang sesuai untuk kategori produk tersebut (Bed Bath Table, Sports Leisure, dan Watches Gifts). Ini menunjukkan bahwa ada *demand* terhadap kategori tersebut sehingga strategi yang dapat diambil adalah **memfokuskan pencarian penjual yang bergerak di segmen bisnis yang populer, namun sepi penjual**.")

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
    pct = proportions.get('Online Medium', 0)
    pct_str = f'{pct:.1%}'.replace('.', ',')
    st.subheader('Penjual "Online Medium" sebagai Kunci Pertumbuhan')
    st.write(f"Dengan **39% penjual** yang berhasil diakuisisi berada di segmen 'Online Medium', strategi pemasaran harus fokus pada aktivasi & akselerasi mereka. Insentif yang tepat dan kampanye pertumbuhan dapat membuka potensi pendapatan yang signifikan dari segmen ini.")
st.header("Prioritaskan Channel dengan Konversi Cepat untuk Percepatan Akuisisi")
st.markdown("Display dan direct traffic terbukti menghasilkan seller lebih cepat. Mengalihkan fokus dan anggaran ke channel berkonversi cepat akan memperpendek siklus akuisisi dan mempercepat pertumbuhan *seller* berkualitas.")
df = pd.merge(deals, leads[['mql_id', 'first_contact_date', 'origin']], on='mql_id', how='left')
df['conversion_days'] = (df['won_date'] - df['first_contact_date']).dt.days
avg_conversion = df.groupby('origin')['conversion_days'].mean().sort_values(ascending=False).reset_index()

fig = px.bar(
    avg_conversion,
    x='conversion_days', y='origin',
    orientation='h',
    color='conversion_days',
    color_continuous_scale='blues',
    labels={'conversion_days': 'Rata-rata Hari Konversi', 'origin': 'Channel (Origin)'},
    title='Rata-rata Waktu Konversi Lead Menjadi Seller per Channel (Origin)',
    template=PLOTLY_TEMPLATE
)
fig.update_traces(text=avg_conversion['conversion_days'].round(1), textposition='outside')
fig.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.header("Apa yang Dapat Kita Simpulkan?")

st.markdown("""
Analisis dasbor e-commerce Brasil menyoroti tiga temuan kunci:

1.  **Kinerja Logistik:** **Rata-rata delay masih 9,4 hari** dengan mayoritas *lead-time* terjadi pada tahap **kurir-ke-pelanggan**.

2.  **Biaya Pengiriman:** **Beban ongkos kirim** yang tinggi (relatif terhadap harga produk) terbukti secara konsisten **menurunkan skor ulasan** seiring dengan kenaikan biaya.

3.  **Kesenjangan Pasar:** Terdapat **ketimpangan *supply-demand*** di mana permintaan pelanggan sangat beragam, namun *demand* terhadap kategori produk favorit tertentu belum dihadapi oleh penjual di segmen bisnis yhang sama.

Untuk menjaga pertumbuhan dan kepuasan pelanggan, perusahaan perlu mengambil tindakan strategis berikut:

- **Memperketat *Service Level Agreement (SLA)*** dengan mitra logistik dan mempertimbangkan penambahan *hub last-mile* di wilayah dengan keterlambatan tinggi.
- **Menurunkan rasio ongkir** yang dirasakan pelanggan melalui strategi *negosiasi* dengan kurir untuk produk bervolume tinggi atau memberikan *subsidi* pengiriman.
- **Menyeimbangkan akuisisi penjual** dengan merekrut lebih banyak penjual di kategori produk yang sangat diminati namun pasokannya kurang.
""")

st.markdown("---")

st.header("***~~ Close Gaps, Scale Faster, Continue Stronger ~~***")

st.markdown("---")
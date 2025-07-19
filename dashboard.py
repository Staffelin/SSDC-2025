# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from gemini import get_response

# --- Helpers ---
@st.cache_data
def load_data():
    # sesuaikan path jika perlu
    orders           = pd.read_csv("E-commerce/orders_dataset.csv", parse_dates=["order_purchase_timestamp", "order_estimated_delivery_date", "order_delivered_customer_date"])
    order_items      = pd.read_csv("E-commerce/order_items_dataset.csv")
    products         = pd.read_csv("E-commerce/products_dataset.csv")
    cat_trans        = pd.read_csv("E-commerce/product_category_name_translation.csv")
    customers        = pd.read_csv("E-commerce/customers_dataset.csv")
    payments         = pd.read_csv("E-commerce/order_payments_dataset.csv")
    reviews          = pd.read_csv("E-commerce/order_reviews_dataset.csv", parse_dates=["review_creation_date", "review_answer_timestamp"])
    mql              = pd.read_csv("E-commerce/marketing_qualified_leads_dataset.csv", parse_dates=["first_contact_date"])
    deals            = pd.read_csv("E-commerce/closed_deals_dataset.csv", parse_dates=["won_date"])
    geolocation      = pd.read_csv("E-commerce/geolocation_dataset.csv")
    sellers          = pd.read_csv("E-commerce/sellers_dataset.csv")
    return orders, order_items, products, cat_trans, customers, payments, reviews, mql, deals, geolocation, sellers

# load
orders, order_items, products, cat_trans, customers, payments, reviews, mql, deals, geolocation, sellers = load_data()

# merge helper
items = order_items.merge(products[["product_id","product_category_name"]], on="product_id", how="left")
items = items.merge(cat_trans, on="product_category_name", how="left")
st.set_page_config(
    page_title="E-commerce Dashboard",
    layout="wide",          # <-- ini yang bikin pakai lebar penuh
    initial_sidebar_state="expanded"
)
# Sidebar: filter periode
# st.sidebar.header("Filter periode")
# min_date = st.sidebar.date_input("Dari", orders["order_purchase_timestamp"].min().date())
# max_date = st.sidebar.date_input("Sampai", orders["order_purchase_timestamp"].max().date())
# mask = (orders["order_purchase_timestamp"].dt.date >= min_date) & (orders["order_purchase_timestamp"].dt.date <= max_date)
# orders = orders[mask]

with st.sidebar:
    st.header("💬 Chatbot")

    # initialize history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # this form will auto-clear its inputs when submitted
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", key="chat_form_input")
        submitted = st.form_submit_button("Send")

        if submitted and user_input:
            # append user message
            st.session_state.chat_history.append(("You", user_input))
            # get bot reply
            bot_reply = get_response(user_input)
            st.session_state.chat_history.append(("Bot", bot_reply))

    # display conversation history
    for speaker, msg in st.session_state.chat_history:
        if speaker == "You":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**Bot:** {msg}")

# --- Revenue Map ---
st.header("Revenue by Geolocation")

# Merge orders, payments, and customers
orders_payments = orders.merge(payments, on='order_id')
df_map = orders_payments.merge(customers, on='customer_id')

# Aggregate geolocation data
geo_agg = geolocation.groupby('geolocation_zip_code_prefix').agg({
    'geolocation_lat': 'mean',
    'geolocation_lng': 'mean'
}).reset_index()

# Merge customer geolocation
df_map = pd.merge(df_map, geo_agg, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', suffixes=(None, '_customer'))

# Merge seller geolocation
sellers_geo = sellers.merge(geo_agg, left_on='seller_zip_code_prefix', right_on='geolocation_zip_code_prefix', suffixes=(None, '_seller'))

# Merge order_items with sellers to get seller_id per order
order_seller = order_items[['order_id', 'seller_id']].merge(sellers_geo[['seller_id', 'geolocation_lat', 'geolocation_lng']], on='seller_id', how='left')
order_seller = order_seller.rename(columns={'geolocation_lat': 'seller_lat', 'geolocation_lng': 'seller_lng'})

# Merge with orders to get customer info
orders_with_seller = orders[['order_id', 'customer_id', 'order_purchase_timestamp']].merge(order_seller, on='order_id', how='left')

# Merge customer geolocation
customers_geo = customers.merge(geo_agg, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
customers_geo = customers_geo.rename(columns={'geolocation_lat': 'customer_lat', 'geolocation_lng': 'customer_lng'})
orders_with_seller = orders_with_seller.merge(customers_geo[['customer_id', 'customer_lat', 'customer_lng']], on='customer_id', how='left')

# Calculate distance in km (Haversine formula)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

orders_with_seller['distance_km'] = haversine(
    orders_with_seller['customer_lat'], orders_with_seller['customer_lng'],
    orders_with_seller['seller_lat'], orders_with_seller['seller_lng']
)

first_orders = (
    orders_with_seller
    .sort_values("order_purchase_timestamp")
    .drop_duplicates("customer_id")
    .loc[:, ["customer_id", "distance_km"]]
)

# orders_with_distance now contains order_id, customer_id, seller_id, order_purchase_timestamp, customer_lat, customer_lng, seller_lat, seller_lng, distance_km
revenue_by_location = df_map.groupby(['geolocation_lat', 'geolocation_lng']).agg(
    total_revenue=('payment_value', 'sum')
).reset_index()

# Create scatter mapbox
fig_map = px.scatter_mapbox(
    revenue_by_location,
    lat="geolocation_lat",
    lon="geolocation_lng",
    size="total_revenue",
    color="total_revenue",
    color_continuous_scale=px.colors.cyclical.IceFire,
    size_max=15,
    zoom=3,
    mapbox_style="carto-positron",
    hover_data={"total_revenue": ":.2f"},
    title="Revenue by Customer Location"
)
fig_map.update_layout(
    mapbox_center={"lat": -14.2350, "lon": -51.9253}, # Center on Brazil
    margin={"r":0,"t":40,"l":0,"b":0}
)



# 1. Tren Revenue & Jumlah Pesanan Bulanan
st.header("📈 Tren Revenue & Jumlah Pesanan Bulanan")
oi = order_items.merge(orders[["order_id","order_purchase_timestamp"]], on="order_id")
oi["month"] = oi["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
monthly = oi.groupby("month").agg(
    revenue = ("price","sum"),
    orders  = ("order_id","nunique")
).reset_index()
col1, col2 = st.columns(2)
fig1 = px.line(monthly, x="month", y="revenue", title="Monthly Revenue")
fig2 = px.line(monthly, x="month", y="orders", title="Monthly Number of Orders")
col1.plotly_chart(fig1, use_container_width=True)
col2.plotly_chart(fig2, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Load your data ---
# Contoh load, sesuaikan path jika perlu!
order_items = pd.read_csv("E-commerce/order_items_dataset.csv")
products = pd.read_csv("E-commerce/products_dataset.csv")
cat_trans = pd.read_csv("E-commerce/product_category_name_translation.csv")

# --- Data preparation & join ---
oi_prod = order_items.merge(
    products[['product_id', 'product_category_name']],
    on='product_id', how='left'
).merge(
    cat_trans, on='product_category_name', how='left'
)
oi_prod['price'] = pd.to_numeric(oi_prod['price'], errors='coerce')
oi_prod = oi_prod.dropna(subset=['product_category_name_english', 'price'])

st.header("Preferensi Pelanggan: Harga & Produk")

unique_cats = sorted(oi_prod['product_category_name_english'].unique())
min_price, max_price = float(oi_prod['price'].min()), float(oi_prod['price'].max())

with st.container():
    col1, col2 = st.columns([3,2])
    with col1:
        selected_cats = st.multiselect(
            "Pilih Kategori Produk:",
            unique_cats,
            default=unique_cats[:6],
            key="produk_filter"
        )
    with col2:
        selected_price = st.slider(
            "Rentang Harga Produk (Rp)",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
            step=100.0,
            key="harga_filter"
        )

oi_filt = oi_prod[
    (oi_prod['product_category_name_english'].isin(selected_cats)) &
    (oi_prod['price'] >= selected_price[0]) &
    (oi_prod['price'] <= selected_price[1])
]

fig_price_dist = px.histogram(
    oi_filt,
    x="price",
    nbins=40,
    title="Distribusi Harga Produk yang Dibeli",
    labels={"price": "Harga Produk (Rp)"},
    color_discrete_sequence=["#118ab2"]
)
st.plotly_chart(fig_price_dist, use_container_width=True)

# --- Visualisasi B: Kategori Produk Favorit ---
fav_cat = (
    oi_filt.groupby('product_category_name_english')
    .agg(jumlah_pembelian=('order_id','count'), revenue=('price','sum'))
    .sort_values('jumlah_pembelian', ascending=False)
    .reset_index()
)

fig_fav_cat = px.bar(
    fav_cat, x='jumlah_pembelian', y='product_category_name_english',
    orientation='h',
    title='Kategori Produk Favorit (Berdasarkan Filter)',
    labels={'jumlah_pembelian': 'Jumlah Pembelian', 'product_category_name_english': 'Kategori'}
)
st.plotly_chart(fig_fav_cat, use_container_width=True)

# --- Visualisasi C: Boxplot Harga per Kategori ---
# (Tampilkan hanya kategori yang muncul di filter)
if len(selected_cats) > 0:
    fig_box = px.box(
        oi_filt,
        x='product_category_name_english', y='price',
        points='outliers',
        title='Distribusi Harga Produk pada Kategori (Sesuai Filter)',
        labels={'product_category_name_english': 'Kategori Produk', 'price': 'Harga (Rp)'}
    )
    fig_box.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("Pilih minimal satu kategori produk untuk melihat distribusi harga per kategori.")

# 3. Peta Panas Revenue per Provinsi
st.header("🌎 Heatmap Revenue per Provinsi")
ord_cust = orders.merge(customers[["customer_id","customer_state"]], on="customer_id")
oi2 = order_items.merge(ord_cust, on="order_id")
prov = oi2.groupby("customer_state").price.sum().reset_index()

# Fetch GeoJSON
geojson_url = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson"

# Create choropleth map
fig4 = px.choropleth(
    prov,
    geojson=geojson_url,
    locations='customer_state',
    featureidkey='properties.sigla',
    color='price',
    color_continuous_scale="Viridis",
    scope="south america",
    title="Revenue by State"
)
fig4.update_geos(fitbounds="locations", visible=False)

# Display two maps side by side
col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue by Geolocation")
    st.plotly_chart(fig_map, use_container_width=True)
with col2:
    st.subheader("Revenue by State")
    st.plotly_chart(fig4, use_container_width=True)

# 4. Distribusi Jenis Pembayaran & Revenue Share
st.header("💳 Distribusi Jenis Pembayaran & Revenue Share")
pay = payments.groupby("payment_type").payment_value.sum().reset_index()
fig4 = px.pie(pay, values="payment_value", names="payment_type", title="Share per Payment Type")
st.plotly_chart(fig4, use_container_width=True)

# 5. Kinerja Pengiriman: Waktu Rata-rata & Persentase Tepat Waktu
st.header("🚚 Kinerja Pengiriman")
deliv = orders.dropna(subset=["order_delivered_customer_date"])
deliv["delivery_time"] = (deliv["order_delivered_customer_date"] - deliv["order_purchase_timestamp"]).dt.days
deliv["on_time"] = deliv["order_delivered_customer_date"] <= deliv["order_estimated_delivery_date"]
avg_time = deliv["delivery_time"].mean()
ontime_rate = deliv["on_time"].mean() * 100
col3, col4 = st.columns(2)
col3.metric("Rata-rata waktu kirim (hari)", f"{avg_time:.1f}")
col4.metric("Persentase on-time", f"{ontime_rate:.1f}%")

# 6. Distribusi Skor Ulasan & Rata-rata per Kategori
st.header("⭐ Distribusi Skor Ulasan")
rev = reviews[["order_id","review_score"]]
rev_cat = rev.merge(items[["order_id","product_category_name_english"]], on="order_id")
score_dist = (
    rev_cat["review_score"]
    .value_counts()
    .sort_index()
    .reset_index(name="count")               # nama kolom count
    .rename(columns={"review_score":"score"})       # ganti 'index' → 'score'
)
fig5 = px.bar(
    score_dist,
    x="score",                               # sekarang ada kolom 'score'
    y="count",                               # dan kolom 'count'
    title="Count per Review Score",
    labels={"score":"Score","count":"Count"}
)
st.plotly_chart(fig5, use_container_width=True)
avg_score = rev_cat.groupby("product_category_name_english").review_score.mean().nlargest(10).reset_index()
fig6 = px.bar(avg_score, x="review_score", y="product_category_name_english", orientation="h", title="Avg Score by Category (Top 10)")
st.plotly_chart(fig6, use_container_width=True)

counts = deals['lead_type'].value_counts().sort_values()
proportions = counts / counts.sum()

# --- Build bar chart ---
fig = px.bar(
    x=proportions.values,
    y=proportions.index,
    orientation='h',
    labels={'x': 'Percentage of Leads', 'y': 'Lead Type'},
    title='Distribusi Lead Type'
)
fig.update_traces(
    text=[f'{p:.1%}' for p in proportions.values],
    textposition='auto'
)
fig.update_layout(
    xaxis_tickformat='.1%',
    margin=dict(l=120, r=20, t=50, b=20)
)

# --- Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    pct = proportions.get('online_medium', 0)
    pct_str = f'{pct:.1%}'.replace('.', ',')  # e.g. "39,7%"

    st.header('Penjual Online-Medium menjadi kunci pertumbuhan')
    st.write(
        f'Dengan {pct_str} penjual berada di online_medium, strategi marketing harus fokus pada '
        'aktivasi & akselerasi mereka. Dorongan insentif dan kampanye pertumbuhan jadi kunci '
        'membuka potensi GMV top-tier.'
    )

# Distribusi Origin MQL (Pie Chart)
st.header("🌐 Distribusi Origin Marketing Qualified Leads")
origin_dist = mql["origin"].value_counts(normalize=True).mul(100).round(1).reset_index()
origin_dist.columns = ["origin", "percentage"]

fig_origin = px.pie(
    origin_dist,
    values="percentage",
    names="origin",
    title="Distribution of MQL Origins (%)",
    hole=0.3
)
st.plotly_chart(fig_origin, use_container_width=True)

st.header("📊 Conversion Rate by MQL Origin")

# Merge MQL dengan closed_deals untuk mengetahui MQL yang berhasil dikonversi
mql_conv = mql[["mql_id", "origin"]].merge(
    deals[["mql_id", "won_date"]],
    on="mql_id", how="left"
)

conv_by_origin = (
    mql_conv.groupby("origin")
    .agg(
        total_leads=("mql_id", "count"),
        deals_closed=("won_date", lambda x: x.notna().sum())
    )
    .reset_index()
)
conv_by_origin["conversion_rate_%"] = (conv_by_origin["deals_closed"] / conv_by_origin["total_leads"] * 100).round(1)

# Sort dari terendah ke tertinggi
conv_by_origin = conv_by_origin.sort_values("conversion_rate_%", ascending=True)

fig_conv_origin = px.bar(
    conv_by_origin,
    x="origin",
    y="conversion_rate_%",
    text="conversion_rate_%",
    title="Conversion Rate by MQL Origin",
    labels={"conversion_rate_%": "Conversion Rate (%)", "origin": "MQL Origin"},
    color="conversion_rate_%"
)
fig_conv_origin.update_traces(texttemplate='%{text}%', textposition='outside')
st.plotly_chart(fig_conv_origin, use_container_width=True)


st.header("📈 Tren Bulanan: MQL vs Closed Deals")

# Bulanan MQL
mql['month'] = mql['first_contact_date'].dt.to_period('M').dt.to_timestamp()
mql_monthly = mql.groupby('month').agg(jumlah_mql=('mql_id', 'count')).reset_index()

# Bulanan Closed Deals
deals['month'] = deals['won_date'].dt.to_period('M').dt.to_timestamp()
deals_monthly = deals.groupby('month').agg(jumlah_deals=('mql_id', 'count')).reset_index()

# Gabungkan
timeline = pd.merge(mql_monthly, deals_monthly, on="month", how="outer").fillna(0).sort_values("month")

fig_trend = px.line(
    timeline,
    x="month",
    y=["jumlah_mql", "jumlah_deals"],
    labels={"value": "Jumlah", "month": "Bulan", "variable": "Tipe"},
    title="Tren Bulanan: Jumlah MQL vs Closed Deals"
)
fig_trend.update_layout(legend_title_text='Tipe')
st.plotly_chart(fig_trend, use_container_width=True)
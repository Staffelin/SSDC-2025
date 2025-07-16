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

# 2. Top 10 Kategori Produk by Revenue
st.header("🏆 Top 10 Kategori Produk by Revenue")
oi_cat = oi.merge(products[["product_id","product_category_name"]], on="product_id")
oi_cat = oi_cat.merge(cat_trans, on="product_category_name")
top_cat = (
    oi_cat
    .groupby("product_category_name_english")
    .agg(revenue=("price", "sum"))          # agregasi price jadi revenue
    .nlargest(10, "revenue")                # ambil 10 terbesar berdasarkan kolom revenue
    .reset_index()
)
fig3 = px.bar(top_cat, x="revenue", y="product_category_name_english", orientation="h", title="Top 10 Categories")
st.plotly_chart(fig3, use_container_width=True)

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

# Distribusi Ukuran Katalog & Perkiraan Pendapatan MQL
st.header("📊 Distribusi Ukuran Katalog & Perkiraan Pendapatan MQL (Marketing Qualified Lead)")
colA, colB = st.columns(2)
with colA:
    fig_catalog = px.histogram(
        deals, x="declared_product_catalog_size", nbins=30,
        title="Distribusi Ukuran Katalog Calon Pelanggan"
    )
    st.plotly_chart(fig_catalog, use_container_width=True)
with colB:
    fig_rev = px.histogram(
        deals, x="declared_monthly_revenue", nbins=510,
        range_x=[0, 5000000],
        title="Distribusi Perkiraan Pendapatan Bulanan MQL"
    )
    st.plotly_chart(fig_rev, use_container_width=True)

# 7. Conversion Funnel MQL → Closed Deals by Origin
st.header("🎯 Conversion Funnel: MQL(Marketing Qualified Lead) → Closed Deals by Origin")
m = mql[["mql_id","origin"]]
d = deals[["mql_id","won_date"]]
funnel = m.merge(d, on="mql_id", how="left").groupby("origin").agg(
    leads       = ("mql_id","count"),
    deals_closed= ("won_date", lambda x: x.notna().sum())
).reset_index()
funnel["conversion_rate %"] = (funnel["deals_closed"]/funnel["leads"]*100).round(1)
st.dataframe(funnel.sort_values("conversion_rate %", ascending=False))

# 7b. Conversion Rate by Seller-Customer Distance
st.header("📏 Conversion Rate by Seller-Customer Distance")

# — 1) Create date‐only columns on deals and orders for matching
deals["won_date_date"]     = deals["won_date"].dt.date
orders["purchase_date"]    = orders["order_purchase_timestamp"].dt.date

# — 2) Join deals → orders to pull in customer_id (one row per mql_id)
deals_orders = (
    deals
    .merge(
        orders[["customer_id", "purchase_date"]],
        left_on="won_date_date",
        right_on="purchase_date",
        how="left"
    )
    .drop_duplicates("mql_id")
)

# — 3) Merge in your precomputed first‐order distance
deals_with_distance = (
    deals_orders
    .merge(
        first_orders[["customer_id", "distance_km"]],
        on="customer_id",
        how="left"
    )
)

# — 4) Attach distance back onto all leads (MQL)
leads_with_distance = (
    mql
    .merge(
        deals_with_distance[["mql_id", "distance_km"]],
        on="mql_id",
        how="left"
    )
)

# — 5) Bin distances and compute conversion rate per band
bins   = [0, 10, 50, 200, np.inf]
labels = ['<10km', '10-50km', '50-200km', '>200km']
leads_with_distance['distance_band'] = pd.cut(
    leads_with_distance['distance_km'],
    bins=bins,
    labels=labels,
    include_lowest=True
)
conv_by_dist = (
    leads_with_distance
    .groupby('distance_band')
    .agg(
        leads=('mql_id', 'count'),
        converted=('distance_km', lambda x: x.notna().sum())
    )
    .reset_index()
)
conv_by_dist['conversion_rate_%'] = (conv_by_dist['converted'] / conv_by_dist['leads'] * 100).round(1)

# — 6) Plot
fig_conv_dist = px.bar(
    conv_by_dist,
    x='distance_band',
    y='conversion_rate_%',
    labels={
      'conversion_rate_%': 'Conversion Rate (%)',
      'distance_band': 'Seller-Customer Distance'
    },
    title='Lead Conversion Rate by Seller-Customer Distance Band'
)
st.plotly_chart(fig_conv_dist, use_container_width=True)

# 8. Rasio Pelanggan Repeat vs New
st.header("🔄 Rasio Pelanggan Repeat vs New")
cust_orders = orders.groupby("customer_id").order_id.nunique().reset_index(name="count_orders")
cust_orders["type"] = np.where(cust_orders["count_orders"]>=2, "Repeat", "New")
ratio = cust_orders["type"].value_counts(normalize=True).mul(100).round(1).reset_index()
ratio.columns = ["type","% of customers"]
fig7 = px.pie(ratio, values="% of customers", names="type", title="New vs Repeat Customers")
st.plotly_chart(fig7, use_container_width=True)

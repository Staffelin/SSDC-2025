# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Helper function to format snake_case names
def format_snake_case(s):
    """Converts snake_case_string to Title Case String."""
    return s.replace('_', ' ').title()

# --- 1. Data Loading and Caching ---
@st.cache_data
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
st.header("🔬 Deep-Dive Analysis")
st.subheader("Analysis Controls")
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
fig_avg.update_layout(
    title=f"Rata-rata Breakdown Waktu Pengiriman ({selected_state})",
    yaxis_title="Rata-rata Waktu (jam)",
    xaxis_title="Proses"
)
st.plotly_chart(fig_avg, use_container_width=True)

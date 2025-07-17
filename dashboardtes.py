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
col1, col2, col3 = st.columns(3)
otd_rate = df_analysis['is_on_time'].mean() * 100
col1.metric("On-Time Delivery (OTD) Rate", f"{otd_rate:.1f}%", help="Percentage of orders delivered to the customer on or before the estimated date.")
seller_adherence_rate = df_analysis['seller_dispatched_on_time'].mean() * 100
col2.metric("Seller On-Time Dispatch", f"{seller_adherence_rate:.1f}%", help="Percentage of items shipped by the seller before the required shipping limit date.")
avg_days_late = df_analysis[~df_analysis['is_on_time']]['days_late'].mean()
col3.metric("Average Customer Days Late", f"{avg_days_late:.1f} days", help="The average delay for orders that were not delivered on time.")

# --- NEW: OTD and Seller Dispatch Rate Trend Over Time ---
st.subheader("📊 Performance Trend Over Time")
df_analysis['month'] = df_analysis['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
monthly_performance = df_analysis.groupby('month').agg(
    customer_otd_rate=('is_on_time', 'mean'),
    seller_dispatch_rate=('seller_dispatched_on_time', 'mean')
).reset_index()
monthly_performance[['customer_otd_rate', 'seller_dispatch_rate']] *= 100

# Melt the dataframe to plot both lines
monthly_performance_melted = monthly_performance.melt(
    id_vars='month',
    value_vars=['customer_otd_rate', 'seller_dispatch_rate'],
    var_name='metric_type',
    value_name='rate'
)
# Rename for clarity in the legend
rename_map = {
    'customer_otd_rate': 'Customer On-Time Rate',
    'seller_dispatch_rate': 'Seller On-Time Dispatch'
}
monthly_performance_melted['metric_type'] = monthly_performance_melted['metric_type'].map(rename_map)

fig_otd_trend = px.line(
    monthly_performance_melted, 
    x='month', 
    y='rate', 
    color='metric_type',
    title="Monthly Performance Rate (%)", 
    markers=True
)
fig_otd_trend.update_layout(yaxis_title="Rate (%)", xaxis_title="Month", legend_title_text='Metric')
st.plotly_chart(fig_otd_trend, use_container_width=True)
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
            bins = list(np.arange(0, 61, 5)) + [np.inf]
            labels = [f"{i} - {i+5}" for i in np.arange(0, 60, 5)] + ["60+"]
            late_data['lateness_bin'] = pd.cut(late_data['days_late'], bins=bins, labels=labels, right=False)
            binned_counts = late_data['lateness_bin'].value_counts().sort_index().reset_index()
            binned_counts.columns = ['lateness_bin', 'count']
            
            fig_dist = px.bar(binned_counts, x='lateness_bin', y='count', text_auto=True, title=f'Distribution of Customer Lateness {category_title}{state_title}')
            fig_dist.update_layout(yaxis_title="Count of Late Orders", xaxis_title='Customer Days Late (Binned)', xaxis={'categoryorder':'array', 'categoryarray': labels})
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No late customer deliveries to display for the selected criteria.")
            
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

# --- NEW: Plot for the most frequently late product categories ---
st.header("Problematic Product Categories")
st.subheader("Top 5 Most Frequently Late Product Categories")
if not df_analysis[~df_analysis['is_on_time']].empty:
    late_categories = df_analysis[~df_analysis['is_on_time']]['product_category_name_english'].value_counts().nlargest(5).reset_index()
    late_categories.columns = ['product_category', 'count_of_late_orders']
    
    fig_late_cats = px.bar(
        late_categories, 
        x='count_of_late_orders', 
        y='product_category',
        orientation='h', 
        title="Top 5 Product Categories with the Most Late Orders",
        text_auto=True
    )
    fig_late_cats.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title='Number of Late Orders', yaxis_title='Product Category')
    st.plotly_chart(fig_late_cats, use_container_width=True)
else:
    st.info("No late orders found.")
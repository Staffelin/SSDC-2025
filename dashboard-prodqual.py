# dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Helper Functions ---
def format_snake_case(s):
    """Converts snake_case_string to Title Case String."""
    if isinstance(s, str):
        return s.replace('_', ' ').title()
    return s

# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    """Loads all necessary e-commerce datasets."""
    path = "E-commerce/"
    orders = pd.read_csv(
        path + "orders_dataset.csv",
        parse_dates=['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
    )
    order_items = pd.read_csv(path + "order_items_dataset.csv")
    products = pd.read_csv(path + "products_dataset.csv")
    cat_trans = pd.read_csv(path + "product_category_name_translation.csv")
    reviews = pd.read_csv(path + "order_reviews_dataset.csv", parse_dates=["review_creation_date", "review_answer_timestamp"])
    return orders, order_items, products, cat_trans, reviews

# Load all data
orders, order_items, products, cat_trans, reviews = load_data()

# --- Data Preparation ---
items = order_items.merge(products, on="product_id", how="left")
items = items.merge(cat_trans, on="product_category_name", how="left")
df_analysis = orders.merge(reviews, on="order_id", how="left")
df_analysis = df_analysis.merge(items, on="order_id", how="left")

# Format and clean data
df_analysis['product_category_name_english'] = df_analysis['product_category_name_english'].dropna().apply(format_snake_case)
df_analysis = df_analysis.dropna(subset=['review_score', 'product_category_name_english', 'review_comment_message', 'order_delivered_customer_date', 'order_estimated_delivery_date'])

# Calculate metrics
df_analysis['days_late'] = (df_analysis['order_delivered_customer_date'] - df_analysis['order_estimated_delivery_date']).dt.total_seconds() / (24 * 3600)
df_analysis['is_late'] = df_analysis['days_late'] > 0

# --- Page Layout and Navigation ---
st.set_page_config(page_title="E-commerce Analysis", layout="wide")

st.sidebar.title("Dashboard Navigation")
page = st.sidebar.radio("Go to:", ["Product Quality Analysis", "Delivery Performance Analysis"])


# --- PAGE 1: PRODUCT QUALITY ANALYSIS ---
if page == "Product Quality Analysis":
    st.title("🔬 Product Quality Analysis Dashboard")

    st.header("Analysis Controls")
    category_list = ['All Categories'] + sorted(df_analysis['product_category_name_english'].dropna().unique().tolist())
    selected_category = st.selectbox("Filter by Product Category:", options=category_list)

    if selected_category != 'All Categories':
        df_filtered = df_analysis[df_analysis['product_category_name_english'] == selected_category]
    else:
        df_filtered = df_analysis.copy()

    st.header(f"Quality Snapshot for: {selected_category}")
    col1, col2 = st.columns([1, 2])
    with col1:
        avg_score = df_filtered['review_score'].mean()
        st.metric("Average Review Score", f"{avg_score:.2f} / 5.0")
    with col2:
        score_dist = df_filtered['review_score'].value_counts().sort_index().reset_index()
        fig_dist = px.bar(score_dist, x='review_score', y='count', text_auto=True, title="Distribution of Customer Review Scores")
        st.plotly_chart(fig_dist, use_container_width=True)
    st.markdown("---")

    st.header("Identifying Best & Worst Performing Categories")
    min_reviews = st.slider("Minimum number of reviews for a category to be shown:", min_value=10, max_value=200, value=50)
    category_quality = df_filtered.groupby('product_category_name_english').agg(average_score=('review_score', 'mean'), review_count=('review_score', 'count')).reset_index()
    category_quality_filtered = category_quality[category_quality['review_count'] >= min_reviews]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Top 5 Highest-Rated Categories")
        top_categories = category_quality_filtered.nlargest(5, 'average_score')
        fig_top = px.bar(top_categories, x='average_score', y='product_category_name_english', orientation='h', text=top_categories['average_score'].apply(lambda x: f'{x:.2f}'))
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Average Score", yaxis_title="Product Category", xaxis=dict(range=[4,5]))
        st.plotly_chart(fig_top, use_container_width=True)
    with col2:
        st.subheader(f"Top 5 Lowest-Rated Categories")
        bottom_categories = category_quality_filtered.nsmallest(5, 'average_score')
        fig_bottom = px.bar(bottom_categories, x='average_score', y='product_category_name_english', orientation='h', text=bottom_categories['average_score'].apply(lambda x: f'{x:.2f}'))
        fig_bottom.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_title="Average Score", yaxis_title="Product Category", xaxis=dict(range=[1,5]))
        st.plotly_chart(fig_bottom, use_container_width=True)
    st.markdown("---")
    
    st.header("Impact of Delivery Performance on Review Scores")
    late_percentage_by_score = df_filtered.groupby('review_score')['is_late'].mean().mul(100).reset_index()
    fig_late_impact = px.bar(late_percentage_by_score, x='review_score', y='is_late', title="Percentage of Orders That Were Late, by Review Score", text_auto='.1f', labels={'review_score': 'Review Score (Stars)', 'is_late': '% of Orders That Were Late'})
    fig_late_impact.update_traces(texttemplate='%{y:.1f}%')
    st.plotly_chart(fig_late_impact, use_container_width=True)
    st.markdown("---")

    # <-- MODIFIED: Replaced Word Cloud with Complaint Categorization Bar Chart -->
    st.header("Understanding Negative Feedback")
    
    # This is the final, refined keyword dictionary using 6 core categories and stem words.

    complaint_keywords = {
        # Focuses only on words related to time and delays.
        "Late Delivery": [
            "atras", "demor", "prazo", "lento", "extravia", "nao chegou"
        ],
        # For orders that never arrived at all. Very specific phrases.
        "Product Not Received": [
            "nao recebi", "nao entregue", "nunca chegou", "consta entregue", "caixa vazia"
        ],
        # Focuses on physical state and function, not general sentiment.
        "Bad Product Quality / Defective": [
            "quebra", "defeit", "nao funciona", "estraga", "avaria", "falso", "acabamento", "desfiando", "queimou", "rasgado"
        ],
        # For when the wrong version, color, or item is sent. 'errado' now lives here.
        "Wrong Item Sent": [
            "diferente", "errado", "outro", "modelo", "cor", "trocado", "versão", "estampa"
        ],
        # Focuses specifically on quantity issues.
        "Missing Items / Partial Delivery": [
            "falta", "incompleto", "apenas", "só", "parte", "unidade", "kit", "parcial", "quantidade"
        ],
        # For issues related to the process of returning items or getting money back.
        "Return & Refund Issues": [
            "devolv", "troca", "dinheiro", "volta", "cancel", "reembolso", "estorno"
        ],
        # Catches complaints about the seller or the company's communication.
        "Poor Customer Service": [
            "vendedor", "loja", "atendimento", "contato", "resposta", "ninguem", "retorno", "pós venda", "soluçao"
        ],
        # This is now the primary home for the general word "entrega".
        "Problems with Carrier / Shipping": [
            "correio", "frete", "transport", "carteiro", "entrega"
        ]
    }

    def categorize_complaint(comment):
        if not isinstance(comment, str): return "Other"
        comment_lower = comment.lower()
        scores = {category: sum(1 for keyword in keywords if keyword in comment_lower) for category, keywords in complaint_keywords.items()}
        max_score = max(scores.values())
        if max_score == 0: return "Other"
        best_category = [category for category, score in scores.items() if score == max_score][0]
        return best_category

    # Filter for low-score reviews (3 stars or less)
    low_score_reviews = df_filtered[df_filtered['review_score'] <= 2].copy()

    if not low_score_reviews.empty:
        low_score_reviews['complaint_category'] = low_score_reviews['review_comment_message'].apply(categorize_complaint)
        category_counts = low_score_reviews['complaint_category'].value_counts().reset_index()
        
        fig_complaints = px.bar(
            category_counts, x='count', y='complaint_category', orientation='h',
            title=f"Top Complaint Categories in Negative Reviews (for {selected_category})", text_auto=True
        )
        fig_complaints.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Number of Negative Reviews", yaxis_title="Complaint Category")
        st.plotly_chart(fig_complaints, use_container_width=True)
    else:
        st.info(f"No negative reviews (2 stars or less) to categorize for '{selected_category}'.")

    # Add this code block right after the bar chart for complaint categories

    # --- Display Sample Comments from "Other" Category ---
    st.subheader("Sample Comments from the 'Other' Category")
    st.write("These are random samples of negative reviews that were not caught by our keyword filters. Analyzing them can help us discover new complaint categories.")

    # Filter for reviews that were categorized as "Other"
    other_reviews = low_score_reviews[low_score_reviews['complaint_category'] == 'Other']

    if not other_reviews.empty:
        # Select a random sample of up to 30 comments
        sample_size = min(30, len(other_reviews))
        sample_comments = other_reviews.sample(n=sample_size, random_state=1)
        
        # Display the relevant columns in a table
        st.dataframe(sample_comments[['review_score', 'review_comment_message']])
    else:
        st.info("No reviews fell into the 'Other' category for the current selection.")


# --- PAGE 2: DELIVERY PERFORMANCE ANALYSIS (placeholder) ---
elif page == "Delivery Performance Analysis":
    st.title("🚚 Delivery Performance Analysis")
    st.write("This page is under construction. You will add the delivery-focused dashboard code here.")
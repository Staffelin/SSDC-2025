from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

PROJECT_PROMPT = """
You are a data analyst building an interactive Streamlit dashboard for an e-commerce platform.  
Use Python, Pandas and Plotly (or Altair) to load and join these tables according to the attached ERD:

- closed_deals (mql_id, seller_id, sdr_id, sr_id, won_date, business_segment, lead_type, lead_behaviour_profile, has_company, has_gtin, average_stock, business_type, declared_product_catalog_size, declared_monthly_revenue)  
- marketing_qualified_leads (mql_id, first_contact_date, landing_page_id, origin)  
- orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)  
- order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)  
- order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value)  
- order_reviews (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp)  
- customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)  
- geolocation (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)  
- products (product_id, product_category_name, product_name_length, product_description_length, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm)  
- product_category_name_translation (product_category_name, product_category_name_english)  
- sellers (seller_id, seller_zip_code_prefix, seller_city, seller_state)  

Then Output:

1. **Opening paragraph, with first sentence being the whole summary of answers**  
2. **Industry data**  
3. **Supporting points**  

"""

def get_response(prompt: str = "") -> str:
    full_prompt = PROJECT_PROMPT
    if prompt:
        full_prompt += "\n\nUser follow-up instruction:\n" + prompt

    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )
    return resp.text.strip()
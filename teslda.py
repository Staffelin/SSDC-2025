import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import time

# --- Configuration ---
REVIEWS_FILE_PATH = "E-commerce/order_reviews_dataset.csv"
NUM_TOPICS = 4  # The number of complaint categories we want to find
TOP_WORDS_PER_TOPIC = 10 # The number of keywords to show for each category

def run_topic_modeling():
    """
    This script performs Topic Modeling on negative customer reviews to
    automatically discover the main categories of complaints.
    """
    print("--- Starting Topic Discovery Process ---")

    # --- Step 1: Load and Prepare Data ---
    print(f"\n[1/5] Loading reviews from '{REVIEWS_FILE_PATH}'...")
    try:
        reviews_df = pd.read_csv(REVIEWS_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: File not found. Make sure '{REVIEWS_FILE_PATH}' exists.")
        return

    # Filter for negative reviews (1 or 2 stars) with comments
    negative_reviews = reviews_df[reviews_df['review_score'] <= 3].dropna(subset=['review_comment_message'])
    
    if negative_reviews.empty:
        print("No negative reviews with comments found. Exiting.")
        return
        
    print(f"Found {len(negative_reviews)} negative reviews with comments to analyze.")

    # --- Step 2: Vectorize Text Data ---
    print("\n[2/5] Converting review text into a numerical format (Vectorizing)...")
    # A list of common Portuguese words to ignore
    stop_words_pt = ['de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'no', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'ao', 'ele', 'das', 'à', 'seu', 'sua', 'ou', 'meu', 'produto']
    
    # This object converts text into a matrix of word counts
    vectorizer = CountVectorizer(max_df=0.9, min_df=5, stop_words=stop_words_pt)
    X = vectorizer.fit_transform(negative_reviews['review_comment_message'])
    print("Vectorizing complete.")

    # --- Step 3: Train the LDA Model ---
    print("\n[3/5] Training the Topic Model to find categories...")
    print("(This step may take a minute...)")
    start_time = time.time()
    
    # Latent Dirichlet Allocation is the algorithm that finds the topics
    lda = LatentDirichletAllocation(n_components=NUM_TOPICS, random_state=42)
    lda.fit(X)
    
    end_time = time.time()
    print(f"Model training complete in {end_time - start_time:.2f} seconds.")

    # --- Step 4: Extract and Display Results ---
    print("\n[4/5] Extracting top words for each discovered topic...")
    feature_names = vectorizer.get_feature_names_out()

    print("\n--- Algorithm Results: Discovered Complaint Topics ---")
    print("Each topic is a collection of words that frequently appear together.")
    print("Your role as the analyst is to give each topic a human-readable name.\n")

    for topic_idx, topic in enumerate(lda.components_):
        # Get the top words for the current topic
        top_words = [feature_names[i] for i in topic.argsort()[:-TOP_WORDS_PER_TOPIC - 1:-1]]
        
        print(f"Topic #{topic_idx + 1}:")
        print("  " + ", ".join(top_words))
        print("-" * 20)

    print("\n[5/5] Process finished.")

# --- Run the script ---
if __name__ == "__main__":
    run_topic_modeling()
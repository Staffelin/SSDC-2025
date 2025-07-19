import pandas as pd
from googletrans import Translator
from tqdm.asyncio import tqdm as aio_tqdm # Use the async-compatible version of tqdm
import asyncio

# --- Configuration ---
INPUT_FILE_PATH = "E-commerce/order_reviews_dataset.csv"
OUTPUT_FILE_PATH = "E-commerce/order_reviews_dataset_translated.csv"
COLUMNS_TO_TRANSLATE = ['review_comment_title', 'review_comment_message']
BATCH_SIZE = 100 # Process N translations at a time

# --- Asynchronous Translation Function ---
async def translate_text_async(text, translator):
    """
    Asynchronously translates a single piece of text.
    Handles potential errors and None values.
    """
    if isinstance(text, str) and text.strip():
        try:
            # 'await' is used to get the result from the coroutine
            translated = await translator.translate(text, src='pt', dest='en')
            return translated.text
        except Exception as e:
            print(f"An error occurred: {e}. Returning original text.")
            return text
    return ""

# --- Main Asynchronous Function ---
async def main():
    """Main function to run the asynchronous translation process."""
    print(f"Reading data from {INPUT_FILE_PATH}...")
    try:
        df = pd.read_csv(INPUT_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE_PATH}")
        return

    print("Initializing translator...")
    translator = Translator()

    for col in COLUMNS_TO_TRANSLATE:
        new_col_name = f"{col}_en"
        print(f"\nTranslating column '{col}' in batches...")
        
        # Get a list of non-null comments to translate
        texts_to_translate = df[col].dropna().tolist()
        
        # Create a list to store translated results
        translated_results = []
        
        # Process in batches to be respectful to the API and manage memory
        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch_texts = texts_to_translate[i:i + BATCH_SIZE]
            
            # Create a list of translation tasks for the current batch
            tasks = [translate_text_async(text, translator) for text in batch_texts]
            
            # Use tqdm.asyncio.gather to run tasks concurrently with a progress bar
            batch_results = await aio_tqdm.gather(*tasks, desc=f"Translating batch {i//BATCH_SIZE + 1}")
            translated_results.extend(batch_results)
            
            # Optional: A small delay between batches
            await asyncio.sleep(1)

        # Create a Series with the translated results, aligning the index with the original non-null data
        translated_series = pd.Series(translated_results, index=df[col].dropna().index)
        
        # Map the translated results back to the original dataframe
        df[new_col_name] = translated_series
        df[new_col_name] = df[new_col_name].fillna("") # Fill any remaining NaNs
        
        print(f"Finished translating column '{col}'.")

    print(f"\nSaving translated data to {OUTPUT_FILE_PATH}...")
    df.to_csv(OUTPUT_FILE_PATH, index=False)

    print("\nTranslation complete!")
    print(f"New file saved at: {OUTPUT_FILE_PATH}")

# --- Run the main asynchronous function ---
if __name__ == "__main__":
    asyncio.run(main())
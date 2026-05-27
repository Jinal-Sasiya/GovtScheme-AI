import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os

# Paths
DATASET_PATH = "../Dataset/myscheme_cleaned.csv"
INDEX_DIR = "./faiss_index"
INDEX_FILE = os.path.join(INDEX_DIR, "schemes.index")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.pkl")

# Ensure index directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

def build_index():
    print(f"Loading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    
    # We will use 'combined_text' if it exists and is not null, otherwise fallback to creating a text
    # Fill missing string values with empty string
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].fillna("")
    
    if 'combined_text' in df.columns:
        texts = df['combined_text'].tolist()
    else:
        print("Column 'combined_text' not found. Creating combined text...")
        texts = []
        for idx, row in df.iterrows():
            text = f"Scheme Name: {row.get('Scheme Name', '')}\n"
            text += f"State: {row.get('State', '')}\n"
            text += f"Ministry: {row.get('Nodal Ministry', '')}\n"
            text += f"Details: {row.get('Details', '')}\n"
            text += f"Eligibility Criteria: {row.get('Eligibility Criteria', '')}\n"
            text += f"Benefits: {row.get('Benefits', '')}\n"
            texts.append(text)
            
    # Remove empty texts if any
    texts = [str(t) for t in texts]

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    print(f"Generating embeddings for {len(texts)} schemes... (this might take a few minutes)")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"Saving FAISS index to {INDEX_FILE}...")
    faiss.write_index(index, INDEX_FILE)
    
    print(f"Saving metadata to {METADATA_FILE}...")
    # Save the dataframe as metadata so we can retrieve the actual scheme details later
    metadata = df.to_dict(orient='records')
    with open(METADATA_FILE, 'wb') as f:
        pickle.dump(metadata, f)
        
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    build_index()

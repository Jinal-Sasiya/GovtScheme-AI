import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer

# Paths
INDEX_DIR = "./faiss_index"
INDEX_FILE = os.path.join(INDEX_DIR, "schemes.index")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.pkl")

class RAGEngine:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.index = None
        self.metadata = None
        self.load_index()
        
        # L2 distance threshold for 'unknown' check. 
        # Since it's L2 distance on unnormalized vectors, we might need a relative threshold.
        # Alternatively, we can use Cosine Similarity if we normalize vectors. 
        # For simplicity, we'll use a distance threshold. Lower is better for L2.
        self.DISTANCE_THRESHOLD = 1.5 

    def load_index(self):
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            print("FAISS index or metadata not found. Please run data_pipeline.py first.")
            return

        print("Loading FAISS index...")
        self.index = faiss.read_index(INDEX_FILE)
        
        print("Loading metadata...")
        with open(METADATA_FILE, 'rb') as f:
            self.metadata = pickle.load(f)
            
    def retrieve(self, query: str, top_k: int = 3):
        if self.index is None or self.metadata is None:
            return []
            
        # Encode query
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i in range(top_k):
            idx = indices[0][i]
            distance = distances[0][i]
            
            # If distance is too high, it means low confidence
            # You can adjust this threshold based on empirical testing
            if distance > self.DISTANCE_THRESHOLD:
                continue
                
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "distance": float(distance),
                    "scheme": self.metadata[idx]
                })
                
        return results

    def format_context(self, retrieved_schemes) -> str:
        if not retrieved_schemes:
            return ""
            
        context = "Here is the relevant information about government schemes:\n\n"
        for idx, item in enumerate(retrieved_schemes):
            scheme = item['scheme']
            name = scheme.get('Scheme Name', 'Unknown Scheme')
            eligibility = scheme.get('Eligibility Criteria', 'N/A')
            benefits = scheme.get('Benefits', 'N/A')
            state = scheme.get('State', 'All')
            details = scheme.get('Details', 'N/A')
            
            context += f"Scheme {idx + 1}: {name}\n"
            context += f"- State: {state}\n"
            context += f"- Eligibility: {eligibility}\n"
            context += f"- Benefits: {benefits}\n"
            context += f"- Details: {details}\n\n"
            
        return context

rag_engine = RAGEngine()

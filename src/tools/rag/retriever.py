import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datasets import load_dataset
from langchain_community.vectorstores import FAISS
from tools.rag.embedder import get_embedder
from config.settings import DATASET_NAME, FAISS_DB_PATH



def build_faiss_index():
    """Build FAISS index from dataset for disease-symptom retrieval."""
    print("📥 Loading dataset...")
    ds = load_dataset(DATASET_NAME, split="train")

    docs = []
    for row in ds:
        disease = row.get("Disease", "")
        symptoms = row.get("Symptoms", "")
        treatments = row.get("Treatments", "")

        text = (
            f"Disease: {disease}\n"
            f"Symptoms: {symptoms}\n"
            f"Treatments: {treatments}"
        )
        docs.append(text)

    print(f"✅ Loaded {len(docs)} records")
    embeddings = get_embedder()

    print("🔧 Building FAISS index...")
    db = FAISS.from_texts(docs, embedding=embeddings)
    db.save_local(FAISS_DB_PATH)
    print(f"✅ Index saved at: {FAISS_DB_PATH}")


def retrieve_semantic_results(query: str, k: int = 3):
    """Retrieve semantically similar medical entries from FAISS."""
    embeddings = get_embedder()
    db = FAISS.load_local(FAISS_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    results = db.similarity_search(query, k=k)
    return [r.page_content for r in results]


if __name__ == "__main__":
    build_faiss_index()


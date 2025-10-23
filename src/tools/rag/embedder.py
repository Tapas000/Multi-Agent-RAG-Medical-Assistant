from langchain_community.embeddings import HuggingFaceEmbeddings
from src.config.settings import EMBED_MODEL

def get_embedder():
    """Return the embedding model instance."""
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)

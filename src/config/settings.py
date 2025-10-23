import os
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL")
DATASET_NAME = os.getenv("DATASET_NAME")
FAISS_DB_PATH = os.getenv("FAISS_DB_PATH")

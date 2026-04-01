from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os
from functools import lru_cache

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


@lru_cache(maxsize=1)
def carregar_model():
    return SentenceTransformer(MODEL_NAME)

def construir_index(chunks_path, index_path):
    print("Carregant model d'embeddings...")
    model = carregar_model()
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    textos = [c["text"] for c in chunks]
    print(f"Generant embeddings per a {len(textos)} fragments...")
    embeddings = model.encode(textos, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, os.path.join(index_path, "index.faiss"))
    with open(os.path.join(index_path, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print("✅ Índex creat!")

def cercar(pregunta, index_path, top_k=5):
    model = carregar_model()
    index_file = os.path.join(index_path, "index.faiss")
    chunks_file = os.path.join(index_path, "chunks.json")

    if not os.path.exists(index_file) or not os.path.exists(chunks_file):
        raise FileNotFoundError("Falten els fitxers de l'índex a data/index")

    index = faiss.read_index(index_file)
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    embedding = model.encode([pregunta]).astype("float32")
    _, indices = index.search(embedding, top_k)
    return [chunks[i] for i in indices[0]]

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    construir_index(
        os.path.join(project_root, "data", "processed", "chunks.json"),
        os.path.join(project_root, "data", "index"),
    )

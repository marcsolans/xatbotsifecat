from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
from functools import lru_cache
from pathlib import Path

from settings import INDEX_DIR, PROCESSED_DIR

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


@lru_cache(maxsize=1)
def carregar_model():
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=4)
def carregar_index_i_chunks(index_path):
    index_path = Path(index_path)
    index_file = index_path / "index.faiss"
    chunks_file = index_path / "chunks.json"

    if not index_file.exists() or not chunks_file.exists():
        raise FileNotFoundError("Falten els fitxers de l'índex a data/index")

    index = faiss.read_index(str(index_file))
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks

def construir_index(chunks_path, index_path):
    print("Carregant model d'embeddings...")
    model = carregar_model()
    chunks_path = Path(chunks_path)
    index_path = Path(index_path)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    textos = [c["text"] for c in chunks]

    if not textos:
        raise ValueError("No hi ha fragments disponibles per construir l'índex")

    print(f"Generant embeddings per a {len(textos)} fragments...")
    embeddings = model.encode(textos, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    index_path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path / "index.faiss"))
    with open(index_path / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    carregar_index_i_chunks.cache_clear()
    print("✅ Índex creat!")

def cercar(pregunta, index_path, top_k=7):
    model = carregar_model()
    index, chunks = carregar_index_i_chunks(index_path)

    if not chunks:
        return []

    embedding = model.encode([pregunta]).astype("float32")
    limit = min(top_k, len(chunks))
    _, indices = index.search(embedding, limit)
    valid_indices = [int(i) for i in indices[0] if 0 <= i < len(chunks)]
    return [chunks[i] for i in valid_indices]

if __name__ == "__main__":
    construir_index(
        PROCESSED_DIR / "chunks.json",
        INDEX_DIR,
    )

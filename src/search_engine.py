from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

def construir_index(chunks_path, index_path):
    print("Carregant model d'embeddings...")
    model = SentenceTransformer(MODEL_NAME)
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
    model = SentenceTransformer(MODEL_NAME)
    index = faiss.read_index(os.path.join(index_path, "index.faiss"))
    with open(os.path.join(index_path, "chunks.json"), "r", encoding="utf-8") as f:
        chunks = json.load(f)
    embedding = model.encode([pregunta]).astype("float32")
    _, indices = index.search(embedding, top_k)
    return [chunks[i] for i in indices[0]]

if __name__ == "__main__":
    construir_index("data/processed/chunks.json", "data/index")

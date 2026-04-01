import fitz
import json
import os

def llegir_pdf(ruta_pdf):
    doc = fitz.open(ruta_pdf)
    text_complet = ""
    for pagina in doc:
        text_complet += pagina.get_text()
    return text_complet

def dividir_en_chunks(text, mida=500):
    paraules = text.split()
    chunks = []
    for i in range(0, len(paraules), mida):
        chunk = " ".join(paraules[i:i+mida])
        chunks.append(chunk)
    return chunks

def processar_pdfs(carpeta_raw, carpeta_processed):
    tots_els_chunks = []
    for arxiu in os.listdir(carpeta_raw):
        if arxiu.endswith(".pdf"):
            print(f"Processant: {arxiu}")
            ruta = os.path.join(carpeta_raw, arxiu)
            text = llegir_pdf(ruta)
            chunks = dividir_en_chunks(text)
            for i, chunk in enumerate(chunks):
                tots_els_chunks.append({
                    "id": f"{arxiu}_{i}",
                    "font": arxiu,
                    "text": chunk
                })
    sortida = os.path.join(carpeta_processed, "chunks.json")
    with open(sortida, "w", encoding="utf-8") as f:
        json.dump(tots_els_chunks, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(tots_els_chunks)} fragments guardats a {sortida}")
    return tots_els_chunks

if __name__ == "__main__":
    processar_pdfs("data/raw", "data/processed")

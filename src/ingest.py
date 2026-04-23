import fitz
import json
from pathlib import Path

from settings import PROCESSED_DIR, RAW_DIR

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def llegir_pdf(ruta_pdf):
    text_complet = ""
    with fitz.open(ruta_pdf) as doc:
        for pagina in doc:
            text_complet += pagina.get_text()
    return text_complet


def llegir_text(ruta_text):
    return Path(ruta_text).read_text(encoding="utf-8", errors="ignore")


def llegir_document(ruta_document):
    suffix = Path(ruta_document).suffix.lower()
    if suffix == ".pdf":
        return llegir_pdf(ruta_document)
    if suffix in {".txt", ".md"}:
        return llegir_text(ruta_document)
    raise ValueError(f"Format no suportat: {suffix}")

def dividir_en_chunks(text, mida=500):
    paraules = text.split()
    chunks = []
    for i in range(0, len(paraules), mida):
        chunk = " ".join(paraules[i:i+mida])
        chunks.append(chunk)
    return chunks

def processar_documents(carpeta_raw, carpeta_processed):
    carpeta_raw = Path(carpeta_raw)
    carpeta_processed = Path(carpeta_processed)

    if not carpeta_raw.exists():
        raise FileNotFoundError(f"No s'ha trobat la carpeta de documents: {carpeta_raw}")

    carpeta_processed.mkdir(parents=True, exist_ok=True)
    tots_els_chunks = []
    rutes_documents = [
        ruta
        for ruta in sorted(carpeta_raw.iterdir())
        if ruta.is_file() and ruta.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    for ruta in rutes_documents:
        arxiu = ruta.name
        print(f"Processant: {arxiu}")
        text = llegir_document(ruta)
        chunks = dividir_en_chunks(text)
        for i, chunk in enumerate(chunks):
            tots_els_chunks.append({
                "id": f"{arxiu}_{i}",
                "font": arxiu,
                "text": chunk
            })
    if not tots_els_chunks:
        raise ValueError(f"No s'ha trobat cap document compatible amb contingut a {carpeta_raw}")

    sortida = carpeta_processed / "chunks.json"
    with open(sortida, "w", encoding="utf-8") as f:
        json.dump(tots_els_chunks, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(tots_els_chunks)} fragments guardats a {sortida}")
    return tots_els_chunks


def processar_pdfs(carpeta_raw, carpeta_processed):
    return processar_documents(carpeta_raw, carpeta_processed)

if __name__ == "__main__":
    processar_documents(RAW_DIR, PROCESSED_DIR)

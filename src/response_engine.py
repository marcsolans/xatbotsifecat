import os
from groq import Groq

def carregar_api_key():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, "r") as f:
        for linia in f:
            if linia.startswith("GROQ_API_KEY="):
                return linia.strip().split("=", 1)[1]
    raise ValueError("No s'ha trobat GROQ_API_KEY al fitxer .env")

def generar_resposta(pregunta, fragments):
    api_key = carregar_api_key()
    client = Groq(api_key=api_key)
    context = "\n\n".join([f["text"] for f in fragments])
    prompt = f"""Ets un assistent expert en el sistema SIFECAT de gestió de fons FEDER de Catalunya.
Respon la pregunta basant-te únicament en el context proporcionat.
Si la informació no està al context, indica-ho clarament.
Respon sempre en el mateix idioma que la pregunta (català o castellà).

Context:
{context}

Pregunta: {pregunta}

Resposta:"""

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return resposta.choices[0].message.content


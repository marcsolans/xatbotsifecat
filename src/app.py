import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))
from search_engine import cercar
from response_engine import generar_resposta

st.set_page_config(page_title="Chatbot SIFECAT", page_icon="🤖")
st.title("🤖 Chatbot SIFECAT")
st.caption("Assistent per a la gestió de fons FEDER de Catalunya")

if "missatges" not in st.session_state:
    st.session_state.missatges = []

for msg in st.session_state.missatges:
    with st.chat_message(msg["rol"]):
        st.write(msg["text"])

pregunta = st.chat_input("Fes una pregunta sobre SIFECAT...")

if pregunta:
    with st.chat_message("user"):
        st.write(pregunta)
    st.session_state.missatges.append({"rol": "user", "text": pregunta})

    with st.chat_message("assistant"):
        with st.spinner("Cercant resposta..."):
            try:
                fragments = cercar(pregunta, "data/index")
                resposta = generar_resposta(pregunta, fragments)
                st.write(resposta)
                st.session_state.missatges.append({"rol": "assistant", "text": resposta})
            except Exception as e:
                st.error(f"Error: {e}")

import streamlit as st
import requests
from typing import Dict, Any

# Configure premium UI settings
st.set_page_config(
    page_title="Quoris — Payment APIs RAG Assistant",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    .reportview-container {
        background: #0F172A;
    }
    .stChatInput {
        border-radius: 12px;
    }
    .citation-box {
        background-color: #1E293B;
        border-left: 4px solid #3B82F6;
        padding: 12px;
        margin-top: 10px;
        border-radius: 0 8px 8px 0;
        font-size: 0.9em;
    }
    .metric-badge {
        background-color: #1E293B;
        color: #60A5FA;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8em;
    }
    .sidebar-status {
        padding: 10px;
        border-radius: 8px;
        background-color: #1E293B;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000/api/v1"

st.title("💳 Quoris — Asistente RAG sobre APIs de Pago")
st.caption("Asistente conversacional con grounding riguroso y citación exacta para integradores de pasarelas de pago.")

# Sidebar status & settings
with st.sidebar:
    st.header("⚙️ Configuración y Estado")
    
    # Check FastAPI backend status
    backend_online = False
    status_data = {}
    try:
        res = requests.get(f"{API_URL}/status", timeout=2)
        if res.status_code == 200:
            status_data = res.json()
            backend_online = True
    except Exception:
        pass
        
    if backend_online:
        st.markdown(
            f'<div class="sidebar-status">'
            f'🟢 <b>Backend:</b> En línea<br>'
            f'📦 <b>Chunks indexados:</b> {status_data.get("indexed_chunks_count", 0)}<br>'
            f'🔑 <b>API Groq:</b> {"Disponible" if status_data.get("has_groq_key") else "Faltante"}'
            f'</div>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="sidebar-status" style="border-left: 4px solid #EF4444;">'
            '🔴 <b>Backend:</b> Fuera de línea<br>'
            '<i>Ejecuta el servidor FastAPI (src/api.py) para comenzar.</i>'
            '</div>', 
            unsafe_allow_html=True
        )
        
    # Provider Filter Option
    provider_filter = st.selectbox(
        "Filtrar búsqueda por proveedor:",
        ["Todos", "Wompi", "Stripe", "MercadoPago"]
    )
    
    st.markdown("---")
    st.subheader("💡 Preguntas Frecuentes")
    suggested_questions = [
        "¿Cómo se calcula la firma de integridad de Wompi?",
        "¿Por qué es obligatorio el token de aceptación?",
        "¿Cómo tokenizo una cuenta Nequi?",
        "¿Cuál es el payload JSON de un webhook en Wompi?",
        "¿Cómo verifico que un webhook es de Wompi?"
    ]
    
    selected_question = st.selectbox(
        "Selecciona una pregunta de ejemplo:",
        [""] + suggested_questions
    )

# Maintain chat history state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown("### 📄 Fuentes Citadas")
            for cite in message["citations"]:
                st.markdown(
                    f'<div class="citation-box">'
                    f'<b>{cite["id"]} - {cite["api_provider"].upper()} ({cite["section"]})</b><br>'
                    f'<a href="{cite["source_url"]}" target="_blank">{cite["source_url"]}</a>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# User input query processing
user_query = ""
if selected_question:
    user_query = selected_question
else:
    user_query = st.chat_input("Escribe tu pregunta sobre la integración...")

if user_query:
    # Reset selected question dropdown visually
    selected_question = ""
    
    # 1. User Message
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. Assistant Message (RAG pipeline execution)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("🔍 *Buscando en la documentación y generando respuesta...*")
        
        if not backend_online:
            error_msg = "❌ Error: El backend FastAPI no está respondiendo. Por favor, inicia el backend ejecutando `python -m uvicorn src.api:app --reload` en tu terminal."
            response_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            try:
                # Append provider keyword to query if filtered to enforce routing
                final_query = user_query
                if provider_filter != "Todos":
                    # Prefix provider name to ensure filtering works correctly
                    final_query = f"[{provider_filter}] {user_query}"
                    
                response = requests.post(
                    f"{API_URL}/query",
                    json={"query": final_query},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    latency = data.get("latency_seconds", 0.0)
                    
                    # Update message UI
                    response_placeholder.markdown(answer)
                    
                    # Display citations
                    if citations:
                        st.markdown("### 📄 Fuentes Citadas")
                        for cite in citations:
                            st.markdown(
                                f'<div class="citation-box">'
                                f'<b>{cite["id"]} - {cite["api_provider"].upper()} ({cite["section"]})</b><br>'
                                f'<a href="{cite["source_url"]}" target="_blank">{cite["source_url"]}</a>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                            
                    # Display metadata & latency
                    st.markdown(
                        f'<p style="text-align: right; color: #64748B; font-size: 0.8em;">'
                        f'Latencia del pipeline RAG: <span class="metric-badge">{latency}s</span>'
                        f'</p>',
                        unsafe_allow_html=True
                    )
                    
                    # Append message to state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations
                    })
                    
                else:
                    error_details = response.json().get("detail", "Error desconocido")
                    err_msg = f"❌ Error en el servidor RAG: {error_details}"
                    response_placeholder.markdown(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                    
            except Exception as e:
                err_msg = f"❌ Excepción al consultar el servidor RAG: {str(e)}"
                response_placeholder.markdown(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})

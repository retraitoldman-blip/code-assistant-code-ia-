
# ─────────────────────────────────────────────────────────────
# 1. IMPORTS (niveau racine)
# ─────────────────────────────────────────────────────────────
import streamlit as st
from groq import Groq
from datetime import datetime
import json

# ─────────────────────────────────────────────────────────────
# 2. FONCTIONS (TOUTES AU NIVEAU RACINE - PAS DANS with/sidebar !)
# ─────────────────────────────────────────────────────────────

def authenticate():
    """Gère l'authentification Admin vs Utilisateur"""
    
    def login_submitted():
        entered_code = st.session_state.get("login_code", "")
        if entered_code == st.secrets.get("admin_password", ""):
            st.session_state.update({"authenticated": True, "is_admin": True, "username": "Administrateur"})
            st.success("✅ Connecté en tant qu'Administrateur")
        elif entered_code in st.secrets.get("user_codes", ["PUBLIC2026"]):
            st.session_state.update({"authenticated": True, "is_admin": False, "username": "Utilisateur"})
            st.success("✅ Connecté en tant qu'Utilisateur")
        else:
            st.session_state["authenticated"] = False
            st.error("❌ Code incorrect. Veuillez réessayer.")
    
    def logout():
        st.session_state.update({"authenticated": False, "is_admin": False, "username": None})
        st.rerun()
    
    if "authenticated" not in st.session_state:
        st.session_state.update({"authenticated": False, "is_admin": False, "username": None})
    
    if st.session_state["authenticated"]:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.write(f"👤 **{st.session_state['username']}**")
        with col2:
            if st.button("🚪 Déconnexion", key="logout_btn"):
                logout()
        return True
    else:
        st.title("🔐 Connexion Requise")
        st.write("Bienvenue sur **Mon Assistant Code IA** !")
        st.text_input("🔑 Code d'accès", type="password", on_change=login_submitted, key="login_code", placeholder="Entrez votre code")
        col1, col2 = st.columns(2)
        with col1: st.info("💡 **Utilisateur**\n\nCode : `PUBLIC2026`")
        with col2: st.warning("🔒 **Admin**\n\nContactez le propriétaire")
        return False

def is_admin():
    return st.session_state.get("is_admin", False)

def get_username():
    return st.session_state.get("username", "Inconnu")

def add_microphone_hint():
    """Affiche astuce dictée vocale"""
    st.info("**🎤 Dictée vocale**\n\nChrome/Edge/Safari : Ctrl+Shift+. pour parler !")

def hide_streamlit_menu():
    """Masque le menu Streamlit pour non-admins"""
    if not is_admin():
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            .stDeployButton {display: none;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Ajouter un indice visuel pour la dictée */
.stChatInputContainer textarea {
    padding-right: 40px !important;
}
.mic-hint::after {
    content: " 🎤";
    opacity: 0.6;
    font-size: 0.9em;
}
</style>
<div class="mic-hint"></div>
""", unsafe_allow_html=True)

def speech_input_component(key="speech_input"):
    """
    Composant microphone fonctionnel pour Streamlit Cloud.
    Retourne le texte dicté ou None.
    """
    import streamlit.components.v1 as components
    import hashlib
    
    # ID unique pour ce composant
    comp_id = hashlib.md5(f"{key}_{id(key)}".encode()).hexdigest()[:8]
    
    # HTML/JS du composant
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; padding: 8px; font-family: sans-serif; }}
            .mic-container {{ display: flex; align-items: center; gap: 8px; }}
            #micBtn {{
                background: #f0f2f6; border: 2px solid #ccc;
                border-radius: 50%; width: 40px; height: 40px;
                font-size: 20px; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
                transition: all 0.2s ease;
            }}
            #micBtn:hover {{ background: #e0e2e6; border-color: #999; }}
            #micBtn.listening {{
                background: #ff4444; border-color: #cc0000;
                color: white; animation: pulse 1s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.1); }}
            }}
            #status {{ font-size: 12px; color: #666; margin-left: 8px; }}
        </style>
    </head>
    <body>
        <div class="mic-container">
            <button id="micBtn" title="Cliquez pour parler">🎤</button>
            <span id="status">Prêt</span>
        </div>
        
        <script>
        (function() {{
            const micBtn = document.getElementById('micBtn');
            const status = document.getElementById('status');
            let recognition = null;
            let isListening = false;
            
            // Vérifier le support
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {{
                micBtn.disabled = true;
                micBtn.title = "Reconnaissance vocale non supportée (utilisez Chrome)";
                status.textContent = "❌ Non supporté";
                return;
            }}
            
            recognition = new SpeechRecognition();
            recognition.lang = 'fr-FR';
            recognition.interimResults = true;
            recognition.continuous = false;
            
            recognition.onstart = () => {{
                isListening = true;
                micBtn.classList.add('listening');
                micBtn.innerHTML = '🔴';
                status.textContent = "Écoute...";
            }};
            
            recognition.onresult = (event) => {{
                let finalTranscript = '';
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {{
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {{
                        finalTranscript += transcript;
                    }} else {{
                        interimTranscript += transcript;
                    }}
                }}
                
                const text = finalTranscript || interimTranscript;
                if (text) {{
                    status.textContent = "✓";
                    // Envoyer à Streamlit via postMessage
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        id: '{comp_id}',
                        value: text
                    }}, '*');
                }}
            }};
            
            recognition.onend = () => {{
                isListening = false;
                micBtn.classList.remove('listening');
                micBtn.innerHTML = '🎤';
                status.textContent = "Prêt";
            }};
            
            recognition.onerror = (event) => {{
                isListening = false;
                micBtn.classList.remove('listening');
                micBtn.innerHTML = '🎤';
                status.textContent = "❌ " + event.error;
                if (event.error === 'not-allowed') {{
                    alert("❌ Microphone bloqué. Veuillez autoriser l'accès dans les paramètres du site.");
                }}
            }};
            
            micBtn.onclick = () => {{
                if (isListening) {{
                    recognition.stop();
                }} else {{
                    navigator.mediaDevices.getUserMedia({{ audio: true }})
                        .then(() => {{
                            recognition.start();
                        }})
                        .catch(err => {{
                            console.error("Erreur micro:", err);
                            alert("❌ Impossible d'accéder au microphone. Vérifiez les permissions.");
                        }});
                }}
            }};
        }})();
        </script>
    </body>
    </html>
    """
    
    # Afficher le composant
    components.html(html, height=60, width=200)
    
    # Récupérer la valeur via session state (mécanisme Streamlit)
    # Note: Pour une intégration parfaite, on utilise un champ texte classique + bouton séparé
    return None  # Pour l'instant, on affiche juste le bouton

# ─────────────────────────────────────────────────────────────
# 3. VÉRIFICATION AUTHENTIFICATION (après définition des fonctions)
# ─────────────────────────────────────────────────────────────
if not authenticate():
    st.stop()

# ─────────────────────────────────────────────────────────────
# 4. CLÉ API + CSS (après authentification, avant page config)
# ─────────────────────────────────────────────────────────────
groq_key = st.secrets.get("groq_api_key", "")
hide_streamlit_menu()  # ✅ Appelée APRÈS sa définition !

# ─────────────────────────────────────────────────────────────
# 5. CONFIGURATION PAGE
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="🤖 Mon Assistant Code", page_icon="🤖", layout="wide")
st.title("🤖 Mon Assistant Code IA")
st.caption("💡 Posez vos questions en Python, JavaScript, HTML, CSS, etc.")

# ─────────────────────────────────────────────────────────────
# 6. CONFIGURATION GROQ + SESSION_STATE
# ─────────────────────────────────────────────────────────────
GROQ_PRICING = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "openai/gpt-oss-20b": {"input": 0.20, "output": 0.20},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "Tu es un expert en code Python."}]
if "token_stats" not in st.session_state:
    st.session_state.token_stats = {"total_input": 0, "total_output": 0, "total_cost": 0.0, "requests": 0}
if "code_to_analyze" not in st.session_state:
    st.session_state.code_to_analyze = None

# ─────────────────────────────────────────────────────────────
# 7. SIDEBAR (SEULEMENT APPELS DE FONCTIONS, PAS DÉFINITIONS !)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Assistant Code")
    st.write(f"👤 {get_username()}")
    st.divider()
    
    model_choice = st.selectbox("🧠 Modèle IA", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "openai/gpt-oss-20b"], index=0)
    st.divider()
    
    if st.button("🗑️ Nouveau Chat", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": "Tu es un expert en code Python."}]
        st.session_state.token_stats = {"total_input": 0, "total_output": 0, "total_cost": 0.0, "requests": 0}
        st.rerun()
    
    st.divider()
    uploaded_file = st.file_uploader("📁 Analyser un fichier", type=["py", "js", "html", "css", "json", "txt", "md"])
    
    # 🎤 Astuce dictée vocale (APPEL de fonction, pas définition !)
    add_microphone_hint()

    
    # Champ texte pour dictée (alternative)
    speech_text = st.text_area(
    "🎤 Dicte ici puis copie-colle :",
    height=70,
    placeholder="Clique ici, puis Ctrl+Shift+. pour parler..."
    )
    
    if speech_text and st.button("➤ Envoyer la dictée", use_container_width=True):
        st.session_state["auto_analyze_prompt"] = speech_text
        st.rerun()
    
    # 🔐 Admin only
    if is_admin():
        st.divider()
        st.subheader("🔐 Administration")
        with st.expander("📊 Statistiques", expanded=True):
            st.write(f"🔄 Requêtes: {st.session_state.token_stats['requests']}")
            st.write(f"💰 Coût: ${st.session_state.token_stats['total_cost']:.4f}")
        if st.button("🔴 Reset Admin", use_container_width=True, type="primary"):
            st.session_state.messages = [{"role": "system", "content": "Tu es un expert en code Python."}]
            st.session_state.token_stats = {"total_input": 0, "total_output": 0, "total_cost": 0.0, "requests": 0}
            st.rerun()

# ─────────────────────────────────────────────────────────────
# 8. AFFICHAGE MESSAGES
# ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────
# 9. CHAT INPUT + TRAITEMENT
# ─────────────────────────────────────────────────────────────
prompt = st.chat_input("Pose ta question... (💡 Ctrl+Shift+. pour dicter)", key="user_question")

if prompt and groq_key and groq_key.startswith("gsk_"):
    valid_models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "mixtral-8x7b-32768"]
    if model_choice not in valid_models:
        st.error(f"⚠️ Modèle invalide")
        st.stop()
    
    context = ""
    if st.session_state.code_to_analyze:
        code = st.session_state.code_to_analyze
        lang = code["extension"][1:] if code["extension"] else "text"
        context = f"[Fichier: {code['name']}]\n```{lang}\n{code['content']}\n```\n\n"
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": context + prompt})
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            client = Groq(api_key=groq_key, timeout=45)
            response = client.chat.completions.create(model=model_choice, messages=st.session_state.messages, temperature=0.3, max_tokens=4096, stream=True)
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)[:150]}")

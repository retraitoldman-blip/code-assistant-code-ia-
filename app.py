        
import streamlit as st
from groq import Groq
from datetime import datetime
import json 

# ─────────────────────────────────────────────────────────────
# 🎤 COMPOSANT SPEECH-TO-TEXT (Web Speech API)
# ─────────────────────────────────────────────────────────────

def speech_to_text_input(key="speech_input"):
    """
    Crée un champ de texte avec bouton microphone pour la reconnaissance vocale.
    Utilise l'API Web Speech native du navigateur.
    """
    
    # HTML + JavaScript pour la reconnaissance vocale
    st.markdown("""
        <style>
        .stTextInput input {
            padding-right: 50px !important;
        }
        .mic-btn {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.2em;
            padding: 5px;
            z-index: 100;
        }
        .mic-btn.listening {
            color: #ff4444;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: translateY(-50%) scale(1); }
            50% { transform: translateY(-50%) scale(1.2); }
            100% { transform: translateY(-50%) scale(1); }
        }
        </style>
        
        <script>
        // Fonction pour initialiser la reconnaissance vocale
        function initSpeechRecognition(inputId) {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("❌ Votre navigateur ne supporte pas la reconnaissance vocale.\n\nUtilisez Chrome, Edge ou Safari.");
                return;
            }
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.lang = 'fr-FR';  // Langue française
            recognition.interimResults = true;
            recognition.continuous = false;
            
            let isListening = false;
            let inputElement = document.querySelector(`input[id*="${inputId}"]`);
            
            if (!inputElement) {
                // Essaye de trouver l'input par label
                const labels = document.querySelectorAll('label');
                for (let label of labels) {
                    if (label.textContent.includes('Question') || label.textContent.includes('question')) {
                        inputElement = label.nextElementSibling?.querySelector('input');
                        if (inputElement) break;
                    }
                }
            }
            
            recognition.onstart = function() {
                isListening = true;
                const micBtn = document.querySelector(`.mic-btn[data-target="${inputId}"]`);
                if (micBtn) micBtn.classList.add('listening');
            };
            
            recognition.onresult = function(event) {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                if (inputElement) {
                    // Met à jour la valeur et déclenche l'événement change pour Streamlit
                    inputElement.value = transcript;
                    inputElement.dispatchEvent(new Event('input', { bubbles: true }));
                }
            };
            
            recognition.onend = function() {
                isListening = false;
                const micBtn = document.querySelector(`.mic-btn[data-target="${inputId}"]`);
                if (micBtn) micBtn.classList.remove('listening');
            };
            
            recognition.onerror = function(event) {
                console.error("Erreur reconnaissance vocale:", event.error);
                isListening = false;
                const micBtn = document.querySelector(`.mic-btn[data-target="${inputId}"]`);
                if (micBtn) micBtn.classList.remove('listening');
                if (event.error === 'not-allowed') {
                    alert("❌ Microphone bloqué. Veuillez autoriser l'accès au micro.");
                }
            };
            
            // Toggle écoute
            function toggleListening() {
                if (!inputElement) {
                    alert("⚠️ Champ de texte non trouvé. Veuillez recharger la page.");
                    return;
                }
                if (isListening) {
                    recognition.stop();
                } else {
                    // Demande la permission microphone
                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then(() => recognition.start())
                        .catch(err => {
                            console.error("Erreur microphone:", err);
                            alert("❌ Impossible d'accéder au microphone. Vérifiez les permissions.");
                        });
                }
            }
            
            // Attache la fonction au bouton microphone
            const micBtn = document.querySelector(`.mic-btn[data-target="${inputId}"]`);
            if (micBtn) {
                micBtn.onclick = toggleListening;
            }
            
            return { recognition, toggleListening };
        }
        
        // Initialisation au chargement
        document.addEventListener('DOMContentLoaded', function() {
            // Délai pour laisser Streamlit rendre les éléments
            setTimeout(() => {
                initSpeechRecognition("${key}");
            }, 1000);
        });
        </script>
        """, unsafe_allow_html=True)
    
    # Champ de texte Streamlit avec bouton microphone injecté via JS
    prompt = st.chat_input("Pose ta question... (ou clique sur 🎤 pour parler)", key=key)
    
    # Injecte le bouton microphone après le rendu du champ
    st.markdown(f"""
        <script>
        setTimeout(() => {{
            const inputs = document.querySelectorAll('input[id*="{key}"]');
            inputs.forEach(input => {{
                if (!input.parentElement.querySelector('.mic-btn')) {{
                    const micBtn = document.createElement('button');
                    micBtn.className = 'mic-btn';
                    micBtn.setAttribute('data-target', '{key}');
                    micBtn.innerHTML = '🎤';
                    micBtn.title = 'Cliquez pour parler';
                    input.parentElement.style.position = 'relative';
                    input.parentElement.appendChild(micBtn);
                }}
            }});
        }}, 500);
        </script>
        """, unsafe_allow_html=True)
    
    return prompt

def authenticate():
    """Gère l'authentification Admin vs Utilisateur"""
    
    def login_submitted():
        """Vérifie les identifiants"""
        entered_code = st.session_state.get("login_code", "")
        
        # Vérifie si c'est l'admin
        if entered_code == st.secrets.get("admin_password", ""):
            st.session_state["authenticated"] = True
            st.session_state["is_admin"] = True
            st.session_state["username"] = "Administrateur"
            st.success("✅ Connecté en tant qu'Administrateur")
        # Vérifie si c'est un utilisateur valide
        elif entered_code in st.secrets.get("user_codes", ""):
            st.session_state["authenticated"] = True
            st.session_state["is_admin"] = False
            st.session_state["username"] = "Utilisateur"
            st.success("✅ Connecté en tant qu'Utilisateur")
        else:
            st.session_state["authenticated"] = False
            st.error("❌ Code incorrect. Veuillez réessayer.")
    
    def logout():
        """Déconnecte l'utilisateur"""
        st.session_state["authenticated"] = False
        st.session_state["is_admin"] = False
        st.session_state["username"] = None
        st.rerun()
    
    # Initialisation
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["is_admin"] = False
        st.session_state["username"] = None
    
    # Si déjà authentifié, affiche le bouton de déconnexion
    if st.session_state["authenticated"]:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.write(f"👤 **{st.session_state['username']}**")
        with col2:
            if st.button("🚪 Déconnexion", key="logout_btn"):
                logout()
        return True
    
    # Si pas authentifié, affiche le formulaire de connexion
    else:
        st.title("🔐 Connexion Requise")
        st.write("Bienvenue sur **Mon Assistant Code IA** !")
        st.write("Veuillez entrer votre code d'accès pour continuer.")
        
        st.divider()
        
        st.text_input(
            "🔑 Code d'accès",
            type="password",
            on_change=login_submitted,
            key="login_code",
            placeholder="Entrez votre code ici",
            label_visibility="collapsed"
        )
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 **Utilisateur Public**\n\nCode : `PUBLIC2026`")
        with col2:
            st.warning("🔒 **Administrateur**\n\nContactez le propriétaire")
        
        st.caption("🌍 Application accessible mondialement • Développé par Snoussi")
        
        return False

def is_admin():
    """Retourne True si l'utilisateur est admin"""
    return st.session_state.get("is_admin", False)

def get_username():
    """Retourne le nom d'utilisateur"""
    return st.session_state.get("username", "Inconnu")

# ─────────────────────────────────────────────────────────────
# 🔐 VÉRIFICATION D'AUTHENTIFICATION (À PLACER AVANT TOUT LE RESTE)
# ─────────────────────────────────────────────────────────────
if not authenticate():
    st.stop()
def hide_streamlit_menu():
    """Masque le menu Streamlit pour les non-admins"""
    if not is_admin():
        st.markdown("""
            <style>
            /* Masquer le menu principal (3 points) */
            #MainMenu {visibility: hidden;}
            /* Masquer le bouton de déploiement */
            .stDeployButton {display: none;}
            /* Masquer le footer Streamlit */
            footer {visibility: hidden;}
            /* Masquer le bouton d'édition (stylo) */
            header {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)

# Appliquer le CSS
hide_streamlit_menu()


# ─────────────────────────────────────────────────────────────
# 1. CONFIGURATION PAGE
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="🤖 Mon Assistant Code", page_icon="🤖", layout="wide")
st.title("🤖 Mon Assistant Code IA")
st.caption("💡 Posez vos questions en Python, JavaScript, HTML, CSS, etc.")

# ─────────────────────────────────────────────────────────────
# 2. PRIX GROQ (GLOBAL)
# ─────────────────────────────────────────────────────────────
GROQ_PRICING = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "openai/gpt-oss-20b": {"input": 0.20, "output": 0.20},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}

# ─────────────────────────────────────────────────────────────
# 3. INITIALISATION SESSION_STATE (TOUJOURS AU DÉBUT !)
# ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "Tu es un expert en code Python."}]

if "token_stats" not in st.session_state:
    st.session_state.token_stats = {
        "total_input": 0, "total_output": 0, "total_cost": 0.0,
        "requests": 0, "last_reset": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

if "code_to_analyze" not in st.session_state:
    st.session_state.code_to_analyze = None

# ─────────────────────────────────────────────────────────────
# 4. SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Assistant Code")
    st.write(f"👤 {get_username()}")
    
    st.divider()
    
    # Choix du modèle
    model_choice = st.selectbox(
        "🧠 Modèle IA",
        ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "openai/gpt-oss-20b"],
        index=0
    )
    
    st.divider()
    
    # Bouton Nouveau Chat
    if st.button("🗑️ Nouveau Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.token_stats = {"requests": 0, "total_input": 0, "total_output": 0, "total_cost": 0}
        st.rerun()
    
    st.divider()
    
    # Upload de fichiers
    st.subheader("📁 Analyser un fichier")
    uploaded_file = st.file_uploader(
        "Choisissez un fichier",
        type=["py", "js", "html", "css", "json", "txt", "md"],
        help="Formats supportés : Python, JavaScript, HTML, CSS, JSON, TXT, Markdown"
    )
    
    # ──────────────────────────────────────────────────────────
    # 🔐 ÉLÉMENTS ADMIN SEULEMENT
    # ──────────────────────────────────────────────────────────
    
    if is_admin():
        st.divider()
        st.subheader("🔐 Administration")
        
        # Statistiques
        with st.expander("📊 Statistiques d'utilisation", expanded=True):
            st.write(f"🔄 **Requêtes :** {st.session_state.token_stats.get('requests', 0)}")
            st.write(f"📥 **Tokens entrants :** {st.session_state.token_stats.get('total_input', 0)}")
            st.write(f"📤 **Tokens sortants :** {st.session_state.token_stats.get('total_output', 0)}")
            st.write(f"💰 **Coût estimé :** ${st.session_state.token_stats.get('total_cost', 0):.4f}")
        
        # Gestion des utilisateurs
        with st.expander("👥 Gestion Utilisateurs", expanded=False):
            st.write("**Codes utilisateurs actifs :**")
            for code in st.secrets.get("user_codes", ""):
                st.text(f"• {code}")
            st.caption("Pour ajouter/supprimer des codes, modifiez les secrets.")
        
        # Reset complet
        st.divider()
        if st.button("🔴 Reset Complet (Admin)", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.token_stats = {"requests": 0, "total_input": 0, "total_output": 0, "total_cost": 0}
            st.session_state.code_to_analyze = None
            st.success("✅ Données réinitialisées !")
            st.rerun()
        
        # Info admin
        st.divider()
        st.caption("🔒 Accès Administrateur uniquement")

# ─────────────────────────────────────────────────────────────
# 5. AFFICHAGE DES MESSAGES (BOUCLE PROPRE)
# ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────
# 6. CHAT INPUT (AVEC SUPPORT AUTO-ANALYSE)
# ─────────────────────────────────────────────────────────────

# Vérifier si un prompt automatique est défini
if "auto_analyze_prompt" in st.session_state:
    prompt = st.session_state.auto_analyze_prompt
    del st.session_state.auto_analyze_prompt  # Nettoyer après utilisation
    auto_trigger = True
else:
    prompt = speech_to_text_input(key="user_question")
    auto_trigger = False

# Si prompt existe (manuel ou auto)
groq_key = st.secrets.get("groq_api_key", "")
if prompt:
    
    if not groq_key or not groq_key.startswith("gsk_"):
        st.error("⚠️ Clé Groq requise")
        st.stop()
    
     # 2️⃣ ✅ NOUVEAU : Vérification du modèle (INSÉREZ CECI)
    valid_models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "mixtral-8x7b-32768"]
    if model_choice not in valid_models:
        st.error(f"⚠️ Modèle '{model_choice}' non valide. Modèles disponibles: {', '.join(valid_models)}")
        st.stop()
    
    # Préparer le contexte fichier si présent
    context = ""
    display_prompt = prompt
    if st.session_state.code_to_analyze:
        code = st.session_state.code_to_analyze
        lang = code["extension"][1:] if code["extension"] else "text"
        context = f"[Fichier: {code['name']}]\n```{lang}\n{code['content']}\n```\n\n"
        display_prompt = f"📎 **{code['name']}**\n\n{prompt}"
    
    # Afficher message utilisateur
    with st.chat_message("user"):
        st.markdown(display_prompt)
    
    # Ajouter à l'historique
    st.session_state.messages.append({"role": "user", "content": context + prompt})
    
    # Générer réponse
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            client = Groq(api_key=groq_key, timeout=45)
            response = client.chat.completions.create(
                model=model_choice,
                messages=st.session_state.messages,
                temperature=0.3,
                max_tokens=4096,
                stream=True
            )
            
            in_tok, out_tok = 0, 0
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
                if hasattr(chunk, 'x_groq') and chunk.x_groq and chunk.x_groq.usage:
                    in_tok = chunk.x_groq.usage.prompt_tokens
                    out_tok = chunk.x_groq.usage.completion_tokens
            
            placeholder.markdown(full_response)
            
            # Mettre à jour stats
            if in_tok > 0 or out_tok > 0:
                price = GROQ_PRICING.get(model_choice, {"input": 0.05, "output": 0.08})
                cost = (in_tok * price["input"] + out_tok * price["output"]) / 1_000_000
                st.session_state.token_stats["total_input"] += in_tok
                st.session_state.token_stats["total_output"] += out_tok
                st.session_state.token_stats["total_cost"] += cost
                st.session_state.token_stats["requests"] += 1
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)[:150]}")

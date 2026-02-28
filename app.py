
import streamlit as st
from groq import Groq
from datetime import datetime
import json 
##

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
    st.header("⚙️ Configuration")
    
    # Clé API
    if "groq_api_key" in st.secrets:
        groq_key = st.secrets["groq_api_key"]
        st.success("✅ Clé chargée")
    else:
        groq_key = st.text_input("🔑 Clé API Groq", type="password", placeholder="gsk_...")
        if groq_key and groq_key.startswith("gsk_"):
            st.success("✅ Clé valide")
    
    st.markdown("[Obtenir une clé](https://console.groq.com/keys)")
    st.divider()
    
    # Nouveau Chat
    if st.button("🗑️ Nouveau Chat", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": "Tu es un expert en code Python."}]
        st.rerun()
    
    # Modèle
    model_choice = st.selectbox("🧠 Modèle", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"])
    
    st.divider()

    if groq_key and groq_key.startswith("gsk_"):
        if st.button("🧪 Tester la clé API", use_container_width=True):
            try:
                test_client = Groq(api_key=groq_key)
                test_client.models.list()
                st.success("✅ Clé API valide !")
            except Exception as e:
                st.error(f"❌ Clé invalide: {str(e)[:100]}")
    
    # 📊 Stats
    st.subheader("📊 Statistiques")
    stats = st.session_state.token_stats
    c1, c2 = st.columns(2)
    c1.metric("🔄 Requêtes", stats["requests"])
    c1.metric("📥 Input", f"{stats['total_input']:,}")
    c2.metric("📤 Output", f"{stats['total_output']:,}")
    c2.metric("💰 Coût", f"${stats['total_cost']:.6f}")
    st.caption(f"🕐 Depuis : {stats['last_reset']}")
    
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.token_stats = {
            "total_input": 0, "total_output": 0, "total_cost": 0.0,
            "requests": 0, "last_reset": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        st.rerun()
    
    st.divider()
    
    # 📁 Upload de fichiers
    st.subheader("📁 Analyser un fichier")
    uploaded_file = st.file_uploader("Choisissez un fichier", type=["py", "js", "html", "css", "json", "txt", "md"])
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            name = uploaded_file.name
            ext = "." + name.split(".")[-1] if "." in name else ".txt"
            st.session_state.code_to_analyze = {"name": name, "content": content, "extension": ext}
            
            with st.expander(f"👁️ {name}"):
                st.code(content[:300] + "..." if len(content) > 300 else content, language=ext[1:])
            
            # ✅ BOUTON D'ANALYSE AUTOMATIQUE
            if st.button("🔍 Analyser ce fichier", use_container_width=True, type="primary"):
                # Définir le prompt automatique
                st.session_state.auto_analyze_prompt = f"Peux-tu analyser ce fichier '{name}' : trouver les bugs potentiels, suggérer des améliorations, et expliquer ce qu'il fait ?"
                st.rerun()
            
            if st.button("🗑️ Retirer", use_container_width=True):
                st.session_state.code_to_analyze = None
                st.rerun()
        except:
            st.error("❌ Fichier non lisible")

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
    prompt = st.chat_input("Pose ta question ou analyse un fichier...")
    auto_trigger = False

# Si prompt existe (manuel ou auto)
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

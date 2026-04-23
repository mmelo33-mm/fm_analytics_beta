import streamlit as st
from auth import criar_usuario, autenticar_usuario, buscar_usuario

st.set_page_config(page_title="Login - FM Analytics", page_icon="🔐")

# =======================
# VERIFICA SE JÁ ESTÁ LOGADO
# =======================
if 'logado' in st.session_state and st.session_state.logado:
    st.success(f"✅ Logado como {st.session_state.usuario}")
    
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.session_state.usuario_id = None
        st.session_state.usuario = None
        st.rerun()
    
    if st.button("🏠 Ir para Dashboard"):
        st.switch_page("app.py")
    
    st.stop()

# =======================
# TÍTULO
# =======================
st.title("⚽ FM Analytics 26")

tab1, tab2 = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

# =======================
# LOGIN
# =======================
with tab1:
    with st.form("login"):
        usuario = st.text_input("👤 Usuário")
        senha = st.text_input("🔒 Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            user_id = autenticar_usuario(usuario, senha)

            if user_id:
                usuario = buscar_usuario(user_id)

                st.session_state.logado = True
                st.session_state.usuario_id = usuario['id']
                st.session_state.usuario = usuario['usuario']
                st.session_state.plano = usuario['plano']

                st.success("✅ Login realizado!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos. Caso tenha esquecido a sua senha, entre em contato com o suporte.")

# =======================
# REGISTRO
# =======================
with tab2:
    with st.form("registro"):
        nome = st.text_input("👤 Nome")
        usuario_novo = st.text_input("👤 Usuário")
        senha_nova = st.text_input("🔒 Senha (min 6 caracteres)", type="password")
        aceita = st.checkbox("Confirmo que vou criar login")
        submit = st.form_submit_button("Criar Conta Grátis", type="primary")
        
        if submit:
            if len(senha_nova) < 6:
                st.error("❌ Senha muito curta")
            elif not aceita:
                st.error("❌ Marque a confirmação para criar a conta")
            else:
                user_id = criar_usuario(usuario_novo, senha_nova)

                if user_id:
                    st.success("🎉 Conta criada! Faça login.")
                else:
                    st.error("❌ Esse usuário já existe")

# =======================
# FOOTER
# =======================
st.divider()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.caption("📧 E-Mail para contato: onzevirtual1895@gmail.com")

with col2:
    st.caption("🔒 Seus dados estão seguros")

with col3:
    st.link_button("Canal Onze Virtual FC", "https://www.youtube.com/@OnzeVirtual-FC")

with col4:
    st.caption("V 1.11")    







# =======================
# CSS
# =======================

st.markdown("""
    <style>
    div.stFormSubmitButton > button:first-child {
        background-color: #28a745;
        color: white;
        border-radius: 5px;
        border: none;
        height: 3em;
        width: 100%;
    }
    div.stFormSubmitButton > button:first-child:hover {
        background-color: #218838;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

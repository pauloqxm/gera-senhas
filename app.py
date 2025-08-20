import os
from urllib.parse import urlparse
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import select
from db import init_db, get_session, User, Payment
from auth import create_user, authenticate, get_user_by_email
from payments import create_checkout_session, verify_checkout_session
from utils_passwords import generate_password

st.set_page_config(page_title="Gerador de Senhas • SaaS", layout="wide")

@st.cache_resource
def _init_app():
    init_db()
    return True

_init_app()

def _ensure_admin():
    admin_email = st.secrets.get("admin", {}).get("email", "").strip().lower()
    admin_pass = st.secrets.get("admin", {}).get("password", "")
    admin_name = st.secrets.get("admin", {}).get("name", "Admin")
    if not admin_email or not admin_pass:
        return
    with get_session() as db:
        u = get_user_by_email(db, admin_email)
        if not u:
            create_user(db, admin_email, admin_name, admin_pass, is_admin=True, plan="premium")
_ensure_admin()

if "user_id" not in st.session_state:
    st.session_state.user_id = None

def current_user() -> User | None:
    if not st.session_state.user_id:
        return None
    with get_session() as db:
        return db.query(User).filter(User.id == st.session_state.user_id).first()

st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1200px;}
</style>
""", unsafe_allow_html=True)

st.title("🔐 Gerador de Senhas (SaaS)")

params = st.query_params
if params.get("paid_success") == "true" and params.get("session_id"):
    user = current_user()
    if user:
        with get_session() as db:
            ok = verify_checkout_session(db, params.get("session_id"))
            if ok:
                u = db.query(User).filter(User.id == user.id).first()
                if u and u.plan != "premium":
                    u.plan = "premium"
                    db.commit()
                st.success("Pagamento confirmado! Seu plano agora é **premium**.")
            else:
                st.info("Não foi possível confirmar o pagamento. Se já pagou, tente novamente em alguns segundos.")
elif params.get("paid_cancel") == "true":
    st.warning("Pagamento cancelado.")

if not current_user():
    tab_login, tab_register = st.tabs(["Entrar", "Cadastrar"])
    with tab_login:
        st.subheader("Acesse sua conta")
        with st.form("form_login", clear_on_submit=False):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
        if submitted:
            with get_session() as db:
                u = authenticate(db, email, password)
                if u:
                    st.session_state.user_id = u.id
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos.")

    with tab_register:
        st.subheader("Crie sua conta")
        with st.form("form_register"):
            name = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            cpass = st.text_input("Confirmar Senha", type="password")
            submitted = st.form_submit_button("Cadastrar")
        if submitted:
            if not name or not email or not password:
                st.error("Preencha todos os campos.")
            elif password != cpass:
                st.error("As senhas não conferem.")
            else:
                with get_session() as db:
                    if get_user_by_email(db, email):
                        st.error("Já existe uma conta com este e-mail.")
                    else:
                        u = create_user(db, email, name, password, is_admin=False, plan="free")
                        st.success("Conta criada! Faça login para continuar.")
else:
    user = current_user()
    colL, colR = st.columns([3,1])
    with colL:
        st.markdown(f"Olá, **{user.name}** — Plano: **{user.plan}**")
    with colR:
        if st.button("Sair"):
            st.session_state.user_id = None
            st.rerun()

    tabs = ["Gerador de Senhas", "Pagamentos"]
    if user.is_admin:
        tabs.append("Admin")
    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        st.subheader("Gerador de Senhas")

        max_len = 64 if user.plan == "premium" else 12
        max_bulk = 200 if user.plan == "premium" else 1

        with st.form("form_gen"):
            length = st.slider("Tamanho", min_value=6, max_value=max_len, value=min(12, max_len))
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                use_upper = st.checkbox("A-Z", value=True)
            with c2:
                use_lower = st.checkbox("a-z", value=True)
            with c3:
                use_digits = st.checkbox("0-9", value=True)
            with c4:
                use_symbols = st.checkbox("Símbolos", value=False)
            avoid_amb = st.checkbox("Evitar caracteres ambíguos (I, l, 0, O, | ...)", value=True)
            qty = st.number_input("Quantidade", min_value=1, max_value=max_bulk, value=1, help="Premium permite lote.")
            submitted = st.form_submit_button("Gerar")

        if submitted:
            if not any([use_upper, use_lower, use_digits, use_symbols]):
                st.error("Selecione pelo menos um tipo de caractere.")
            else:
                passwords = [generate_password(length, use_upper, use_lower, use_digits, use_symbols, avoid_amb) for _ in range(qty)]
                if qty == 1:
                    pw = passwords[0]
                    st.code(pw, language="text")
                    st.download_button("Baixar .txt", data=pw, file_name="senha.txt")
                else:
                    csv = "password\n" + "\n".join(passwords)
                    st.download_button("Baixar .csv", data=csv, file_name="senhas.csv")
                    st.success(f"Geradas {qty} senhas.")

        st.info("No plano **premium**, você pode gerar senhas mais longas e em lote.")

    with tab_objs[1]:
        st.subheader("Assine o Premium")
        st.write("Desbloqueie senhas maiores, geração em lote e futuras funcionalidades.")

        if user.plan == "premium":
            st.success("Você já é **premium**. Obrigado!")
        else:
            if st.button("Ir para Checkout (Stripe)"):
                with get_session() as db:
                    try:
                        url = create_checkout_session(db, user, quantity=1)
                        st.link_button("Abrir Checkout", url)
                        st.info("Após pagar, você será redirecionado de volta e seu plano será ativado automaticamente.")
                    except Exception as e:
                        st.error(f"Erro criando checkout: {e}")

        st.caption("Se preferir um gateway brasileiro (ex.: Mercado Pago), a lógica é parecida: criar sessão, redirecionar e verificar no retorno.")

    if user.is_admin:
        with tab_objs[2]:
            st.subheader("Painel Administrativo")
            with get_session() as db:
                users = db.query(User).all()
                pays = db.query(Payment).order_by(Payment.created_at.desc()).all()

            st.markdown("### Usuários")
            import pandas as pd
            df_users = pd.DataFrame([{
                "id": u.id, "email": u.email, "nome": u.name, "admin": u.is_admin, "plano": u.plan, "criado_em": u.created_at
            } for u in users])
            st.dataframe(df_users, use_container_width=True, hide_index=True)

            st.markdown("### Pagamentos")
            df_pay = pd.DataFrame([{
                "id": p.id, "user_id": p.user_id, "status": p.status, "provider": p.provider,
                "checkout_session_id": p.checkout_session_id, "intent": p.payment_intent_id,
                "criado_em": p.created_at, "atualizado_em": p.updated_at
            } for p in pays])
            st.dataframe(df_pay, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### Ações")
            with get_session() as db:
                emails = [u.email for u in db.query(User).all()]
            target = st.selectbox("Selecionar usuário por e-mail", options=emails if emails else ["-"])
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Tornar Admin"):
                    with get_session() as db:
                        u = get_user_by_email(db, target)
                        if u:
                            u.is_admin = True
                            db.commit()
                            st.success(f"{u.email} agora é admin.")
                            st.rerun()
            with col2:
                if st.button("Remover Admin"):
                    with get_session() as db:
                        u = get_user_by_email(db, target)
                        if u:
                            u.is_admin = False
                            db.commit()
                            st.success(f"{u.email} não é mais admin.")
                            st.rerun()
            with col3:
                new_plan = st.selectbox("Plano", options=["free", "premium"], index=0, key="planselect")
                if st.button("Alterar Plano"):
                    with get_session() as db:
                        u = get_user_by_email(db, target)
                        if u:
                            u.plan = new_plan
                            db.commit()
                            st.success(f"Plano de {u.email} atualizado para {new_plan}.")
                            st.rerun()

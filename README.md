# 🔐 Gerador de Senhas — SaaS em Streamlit (Cadastro, Autenticação, Pagamentos, Admin)

Sistema completo em **Python + Streamlit** com:
- Cadastro e login de usuários (hash seguro com bcrypt)
- Gerador de senhas (free vs. premium)
- Integração com **Stripe Checkout** (assinatura ou pagamento único)
- Painel Administrativo (gerenciar usuários e pagamentos)
- Banco de dados via **SQLAlchemy** (SQLite para dev / Postgres para produção)

## 🚀 Rodar localmente
1. Ambiente virtual e deps
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
2. Ajuste `.streamlit/secrets.toml`.
3. Rode: `streamlit run app.py`

## ☁️ Deploy no Streamlit Cloud
- Suba no GitHub, crie app no Streamlit Cloud e cole os **Secrets**.
- Opcional: use Postgres gerenciado (Neon) via `DATABASE_URL`.

## 💳 Stripe
- Crie Product/Price e copie `price_id`. Em `secrets.toml` preencha `secret_key` e `price_id`.
- Após pagar, o Stripe redireciona para `/?paid_success=true&session_id=...`. O app verifica e ativa o **premium**.

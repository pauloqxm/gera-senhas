import streamlit as st
import pandas as pd
import random
import string
import hashlib
import json
from datetime import datetime, timedelta
import requests
import base64
import time

# Configuração da página
st.set_page_config(
    page_title="Sistema de Pagamentos com Status",
    page_icon="💳",
    layout="wide"
)

# Configurações (substitua com suas informações)
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "ghp_seu_token_aqui")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "seu_usuario/nome_repositorio")
GITHUB_USER = st.secrets.get("GITHUB_USER", "seu_usuario")

# Funções de utilidade
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_senha(tamanho=12, usar_maiusculas=True, usar_numeros=True, usar_especiais=True):
    caracteres = string.ascii_lowercase
    if usar_maiusculas:
        caracteres += string.ascii_uppercase
    if usar_numeros:
        caracteres += string.digits
    if usar_especiais:
        caracteres += string.punctuation
    
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

# Funções de integração com GitHub
def github_get_file(filename):
    """Busca um arquivo do repositório GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            return base64.b64decode(content).decode("utf-8")
    except:
        pass
    return None

def github_save_file(filename, content, message="Update file"):
    """Salva um arquivo no repositório GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Verifica se o arquivo já existe para obter o SHA
    sha = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json()["sha"]
    except:
        pass
    
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    
    try:
        response = requests.put(url, headers=headers, json=data)
        return response.status_code == 200 or response.status_code == 201
    except:
        return False

def carregar_usuarios():
    """Carrega usuários do GitHub"""
    usuarios_data = github_get_file("usuarios.json")
    if usuarios_data:
        return json.loads(usuarios_data)
    return {}

def salvar_usuarios(usuarios):
    """Salva usuários no GitHub"""
    return github_save_file("usuarios.json", json.dumps(usuarios, indent=2), "Atualização de usuários")

def carregar_pagamentos():
    """Carrega pagamentos do GitHub"""
    pagamentos_data = github_get_file("pagamentos.json")
    if pagamentos_data:
        return json.loads(pagamentos_data)
    return []

def salvar_pagamentos(pagamentos):
    """Salva pagamentos no GitHub"""
    return github_save_file("pagamentos.json", json.dumps(pagamentos, indent=2), "Atualização de pagamentos")

# Funções de processamento de pagamento
def simular_processamento_pagamento(metodo, valor):
    """Simula o processamento de um pagamento com diferentes resultados"""
    # Simula atraso no processamento
    time.sleep(2)
    
    # Probabilidades baseadas no método de pagamento
    if metodo == "Cartão de Crédito":
        # 80% de aprovação para cartão
        aprovado = random.random() < 0.8
    elif metodo == "PIX":
        # 95% de aprovação para PIX
        aprovado = random.random() < 0.95
    else:  # Boleto
        # 70% de aprovação para boleto
        aprovado = random.random() < 0.7
    
    if aprovado:
        return "Aprovado"
    else:
        # Razões para reprovação
        razoes = ["Saldo insuficiente", "Problema técnico", "Transação suspeita", "Dados inválidos"]
        return f"Reprovado - {random.choice(razoes)}"

def atualizar_status_pagamentos():
    """Atualiza automaticamente o status dos pagamentos pendentes"""
    pagamentos = carregar_pagamentos()
    atualizados = False
    
    for pagamento in pagamentos:
        if pagamento["status"] == "Pendente":
            # Simula a passagem do tempo
            data_criacao = datetime.fromisoformat(pagamento["data_criacao"])
            tempo_decorrido = datetime.now() - data_criacao
            
            # Se passou mais de 1 minuto, processa o pagamento
            if tempo_decorrido.total_seconds() > 60:
                pagamento["status"] = simular_processamento_pagamento(
                    pagamento["metodo"], pagamento["valor"]
                )
                pagamento["data_processamento"] = datetime.now().isoformat()
                atualizados = True
    
    if atualizados:
        salvar_pagamentos(pagamentos)
    
    return atualizados

# Interface Streamlit
def main():
    st.title("💳 Sistema de Pagamentos com Identificação de Status")
    
    if 'usuario_logado' not in st.session_state:
        st.session_state.usuario_logado = None
    
    # Atualizar status de pagamentos pendentes
    if atualizar_status_pagamentos():
        st.rerun()
    
    # Menu principal
    menu = ["Login", "Cadastro", "Gerar Senha", "Pagamentos", "Meus Pagamentos", "Sair", "Admin"]
    escolha = st.sidebar.selectbox("Menu", menu)
    
    # Inicializar dados
    usuarios = carregar_usuarios()
    pagamentos = carregar_pagamentos()
    
    if escolha == "Cadastro" and not st.session_state.usuario_logado:
        st.header("📝 Cadastro de Usuário")
        
        with st.form("form_cadastro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted:
                if senha != confirmar_senha:
                    st.error("As senhas não coincidem!")
                elif len(senha) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres!")
                elif email in usuarios:
                    st.error("Email já cadastrado!")
                else:
                    usuarios[email] = {
                        "nome": nome,
                        "senha_hash": hash_senha(senha),
                        "data_cadastro": datetime.now().isoformat()
                    }
                    if salvar_usuarios(usuarios):
                        st.success("Cadastro realizado com sucesso!")
                    else:
                        st.error("Erro ao salvar no GitHub!")
    
    elif escolha == "Login" and not st.session_state.usuario_logado:
        st.header("🔑 Login")
        
        with st.form("form_login"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            
            submitted = st.form_submit_button("Entrar")
            
            if submitted:
                if email in usuarios and usuarios[email]["senha_hash"] == hash_senha(senha):
                    st.session_state.usuario_logado = {
                        "email": email,
                        "nome": usuarios[email]["nome"]
                    }
                    st.success(f"Bem-vindo, {usuarios[email]['nome']}!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas!")
    
    elif escolha == "Gerar Senha":
        st.header("🔑 Gerador de Senhas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tamanho = st.slider("Tamanho da senha", 8, 32, 12)
            usar_maiusculas = st.checkbox("Incluir letras maiúsculas", value=True)
            usar_numeros = st.checkbox("Incluir números", value=True)
            usar_especiais = st.checkbox("Incluir caracteres especiais", value=True)
            
            if st.button("Gerar Senha"):
                senha_gerada = gerar_senha(tamanho, usar_maiusculas, usar_numeros, usar_especiais)
                st.session_state.senha_gerada = senha_gerada
        
        with col2:
            if 'senha_gerada' in st.session_state:
                st.success("Senha gerada com sucesso!")
                st.code(st.session_state.senha_gerada)
                st.info("⚠️ Guarde esta senha em local seguro!")
                
                # Teste de força da senha
                forca = 0
                if any(c.isupper() for c in st.session_state.senha_gerada):
                    forca += 1
                if any(c.isdigit() for c in st.session_state.senha_gerada):
                    forca += 1
                if any(c in string.punctuation for c in st.session_state.senha_gerada):
                    forca += 1
                if len(st.session_state.senha_gerada) >= 12:
                    forca += 1
                
                if forca == 4:
                    st.success("Força da senha: Excelente 🔒🔒🔒")
                elif forca == 3:
                    st.warning("Força da senha: Boa 🔒🔒")
                else:
                    st.error("Força da senha: Fraca 🔒")
    
    elif escolha == "Pagamentos" and st.session_state.usuario_logado:
        st.header("💳 Sistema de Pagamentos")
        
        with st.form("form_pagamento"):
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            descricao = st.text_input("Descrição do pagamento")
            
            # Simulação de métodos de pagamento
            metodo_pagamento = st.selectbox("Método de Pagamento", 
                                           ["Cartão de Crédito", "PIX", "Boleto Bancário"])
            
            submitted = st.form_submit_button("Realizar Pagamento")
            
            if submitted:
                novo_pagamento = {
                    "id": len(pagamentos) + 1,
                    "usuario_email": st.session_state.usuario_logado["email"],
                    "usuario_nome": st.session_state.usuario_logado["nome"],
                    "valor": valor,
                    "descricao": descricao,
                    "metodo": metodo_pagamento,
                    "status": "Pendente",
                    "data_criacao": datetime.now().isoformat(),
                    "data_processamento": None
                }
                pagamentos.append(novo_pagamento)
                if salvar_pagamentos(pagamentos):
                    st.success(f"Pagamento de R$ {valor:.2f} registrado com sucesso! Aguardando processamento.")
                    
                    # Mostrar informações sobre o processamento
                    with st.expander("ℹ️ Informações sobre o processamento"):
                        st.write("""
                        **Status do pagamento:**
                        - ✅ **Pendente**: Seu pagamento foi registrado e está aguardando processamento.
                        - ⏳ **Processando**: Seu pagamento está sendo processado (leva cerca de 1 minuto).
                        - ✅ **Aprovado**: Seu pagamento foi aprovado com sucesso.
                        - ❌ **Reprovado**: Seu pagamento foi reprovado. Verifique os detalhes para mais informações.
                        
                        Atualize a página ou verifique em 'Meus Pagamentos' para acompanhar o status.
                        """)
                    
                    st.balloons()
                else:
                    st.error("Erro ao salvar no GitHub!")
    
    elif escolha == "Meus Pagamentos" and st.session_state.usuario_logado:
        st.header("📋 Meus Pagamentos")
        
        meus_pagamentos = [p for p in pagamentos if p["usuario_email"] == st.session_state.usuario_logado["email"]]
        
        if meus_pagamentos:
            # Ordenar por data (mais recente primeiro)
            meus_pagamentos.sort(key=lambda x: x["data_criacao"], reverse=True)
            
            # Criar DataFrame para exibição
            df = pd.DataFrame(meus_pagamentos)
            df["data_criacao"] = pd.to_datetime(df["data_criacao"])
            
            # Formatar colunas para exibição
            df_display = df[["id", "valor", "descricao", "metodo", "status", "data_criacao"]].copy()
            df_display["data_criacao"] = df_display["data_criacao"].dt.strftime("%d/%m/%Y %H:%M")
            df_display = df_display.rename(columns={
                "id": "ID",
                "valor": "Valor (R$)",
                "descricao": "Descrição",
                "metodo": "Método",
                "status": "Status",
                "data_criacao": "Data"
            })
            
            # Colorir status
            def color_status(val):
                if "Aprovado" in val:
                    return "color: green; font-weight: bold;"
                elif "Reprovado" in val:
                    return "color: red; font-weight: bold;"
                elif "Pendente" in val:
                    return "color: orange; font-weight: bold;"
                else:
                    return ""
            
            st.dataframe(df_display.style.applymap(color_status, subset=["Status"]), use_container_width=True)
            
            # Estatísticas
            total_pago = df[df["status"].str.contains("Aprovado")]["valor"].sum() if any(df["status"].str.contains("Aprovado")) else 0
            pendentes = len(df[df["status"] == "Pendente"])
            aprovados = len(df[df["status"].str.contains("Aprovado")])
            reprovados = len(df[df["status"].str.contains("Reprovado")])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Pago", f"R$ {total_pago:.2f}")
            with col2:
                st.metric("Pagamentos Pendentes", pendentes)
            with col3:
                st.metric("Pagamentos Aprovados", aprovados)
            with col4:
                st.metric("Pagamentos Reprovados", reprovados)
                
            # Gráfico de status
            status_counts = df["status"].value_counts()
            if not status_counts.empty:
                st.subheader("📊 Distribuição de Status")
                st.bar_chart(status_counts)
        else:
            st.info("Nenhum pagamento registrado ainda.")
    
    elif escolha == "Admin" and st.session_state.usuario_logado and st.session_state.usuario_logado["email"] == "admin@admin.com":
        st.header("👨‍💼 Painel Administrativo")
        
        tab1, tab2, tab3 = st.tabs(["Usuários", "Pagamentos", "Processar Pagamentos"])
        
        with tab1:
            st.subheader("Usuários Cadastrados")
            if usuarios:
                df_usuarios = pd.DataFrame.from_dict(usuarios, orient='index')
                df_usuarios = df_usuarios.reset_index().rename(columns={'index': 'email'})
                st.dataframe(df_usuarios[['email', 'nome', 'data_cadastro']], use_container_width=True)
                st.metric("Total de Usuários", len(usuarios))
            else:
                st.info("Nenhum usuário cadastrado.")
        
        with tab2:
            st.subheader("Todos os Pagamentos")
            if pagamentos:
                df_pagamentos = pd.DataFrame(pagamentos)
                df_pagamentos["data_criacao"] = pd.to_datetime(df_pagamentos["data_criacao"])
                df_display = df_pagamentos[["id", "usuario_nome", "valor", "descricao", "metodo", "status", "data_criacao"]].copy()
                df_display["data_criacao"] = df_display["data_criacao"].dt.strftime("%d/%m/%Y %H:%M")
                
                st.dataframe(df_display.style.applymap(color_status, subset=["Status"]), use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Pagamentos", len(pagamentos))
                with col2:
                    st.metric("Valor Total", f"R$ {df_pagamentos['valor'].sum():.2f}")
                with col3:
                    st.metric("Pagamentos Pendentes", len(df_pagamentos[df_pagamentos['status'] == 'Pendente']))
                    
                # Filtros
                st.subheader("Filtros")
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect("Filtrar por status", options=df_pagamentos["status"].unique(), default=df_pagamentos["status"].unique())
                with col2:
                    metodo_filter = st.multiselect("Filtrar por método", options=df_pagamentos["metodo"].unique(), default=df_pagamentos["metodo"].unique())
                
                filtered_df = df_pagamentos[
                    (df_pagamentos["status"].isin(status_filter)) & 
                    (df_pagamentos["metodo"].isin(metodo_filter))
                ]
                
                if not filtered_df.empty:
                    st.metric("Pagamentos Filtrados", len(filtered_df))
                    st.metric("Valor Filtrado", f"R$ {filtered_df['valor'].sum():.2f}")
            else:
                st.info("Nenhum pagamento registrado.")
                
        with tab3:
            st.subheader("Processamento de Pagamentos")
            st.info("Os pagamentos são processados automaticamente a cada minuto. Você pode forçar o processamento manualmente abaixo.")
            
            pagamentos_pendentes = [p for p in pagamentos if p["status"] == "Pendente"]
            
            if pagamentos_pendentes:
                st.write(f"**Pagamentos pendentes:** {len(pagamentos_pendentes)}")
                
                if st.button("🔄 Processar Pagamentos Pendentes", type="primary"):
                    with st.spinner("Processando pagamentos..."):
                        for pagamento in pagamentos_pendentes:
                            pagamento["status"] = simular_processamento_pagamento(
                                pagamento["metodo"], pagamento["valor"]
                            )
                            pagamento["data_processamento"] = datetime.now().isoformat()
                        
                        if salvar_pagamentos(pagamentos):
                            st.success("Pagamentos processados com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao salvar no GitHub!")
            else:
                st.success("✅ Nenhum pagamento pendente para processar!")
    
    elif escolha == "Sair" and st.session_state.usuario_logado:
        st.session_state.usuario_logado = None
        st.success("Logout realizado com sucesso!")
        st.rerun()
    
    # Status do usuário e informações do GitHub
    if st.session_state.usuario_logado:
        st.sidebar.success(f"👤 Logado como: {st.session_state.usuario_logado['nome']}")
        st.sidebar.info(f"📅 Desde: {datetime.now().strftime('%d/%m/%Y')}")
    else:
        st.sidebar.warning("⚠️ Não logado")
    
    # Informações do GitHub na sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔗 Integração com GitHub")
    st.sidebar.info(f"Repositório: {GITHUB_REPO}")
    
    if st.sidebar.button("🔄 Atualizar Dados do GitHub"):
        usuarios = carregar_usuarios()
        pagamentos = carregar_pagamentos()
        st.sidebar.success("Dados atualizados do GitHub!")
        st.rerun()
        
    # Informações sobre status de pagamento
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Status de Pagamento")
    st.sidebar.info("""
    - ✅ **Pendente**: Aguardando processamento
    - ⏳ **Processando**: Em análise
    - ✅ **Aprovado**: Pagamento confirmado
    - ❌ **Reprovado**: Pagamento não aprovado
    """)

if __name__ == "__main__":
    main()
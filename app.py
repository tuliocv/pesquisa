import os
import json
from datetime import datetime

import pandas as pd
import streamlit as st

# ==========================
# Configurações
# ==========================
st.set_page_config(page_title="Pesquisa de Satisfação", layout="centered")

DATA_DIR = "data"
FILE_PATH = os.path.join(DATA_DIR, "respostas.jsonl")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==========================
# Persistência
# ==========================
def salvar_resposta(resposta: dict) -> None:
    with open(FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(resposta, ensure_ascii=False) + "\n")


def carregar_respostas() -> list[dict]:
    if not os.path.exists(FILE_PATH):
        return []
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        linhas = [ln.strip() for ln in f.readlines() if ln.strip()]
    out: list[dict] = []
    for ln in linhas:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            # Ignora linhas corrompidas
            pass
    return out


# ==========================
# UI
# ==========================
st.sidebar.title("Menu")
modo = st.sidebar.radio("Escolha o modo:", ["Aluno", "Admin"])

# --------------------------
# MODO ALUNO
# --------------------------
if modo == "Aluno":
    st.title("📚 Pesquisa de Satisfação da Aula")
    st.write("Sua opinião é muito importante para melhorar as próximas aulas!")

    with st.form("form_pesquisa"):
        st.subheader("Avalie de 1 a 5")

        nota_clareza = st.slider("1️⃣ A explicação foi clara?", 1, 5, 4)
        nota_dinamica = st.slider("2️⃣ A aula foi dinâmica e interessante?", 1, 5, 4)
        nota_material = st.slider("3️⃣ O material ajudou na compreensão?", 1, 5, 4)

        st.subheader("Percepção geral")
        nivel_dificuldade = st.selectbox(
            "4️⃣ O nível da aula foi:",
            ["Muito fácil", "Adequado", "Difícil"],
            index=1,
        )

        sugestao = st.text_area("5️⃣ O que pode melhorar? (opcional)")

        enviado = st.form_submit_button("Enviar resposta")

    if enviado:
        resposta = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "clareza": int(nota_clareza),
            "dinamica": int(nota_dinamica),
            "material": int(nota_material),
            "nivel": nivel_dificuldade,
            "sugestao": sugestao.strip(),
        }
        salvar_resposta(resposta)
        st.success("✅ Obrigado! Sua resposta foi registrada.")

# --------------------------
# MODO ADMIN (usuário + senha + limpar)
# --------------------------
else:
    st.title("🔐 Área Administrativa")

    # Carrega credenciais de forma segura
    admin_user = None
    admin_password = None

    if "ADMIN_USER" in st.secrets and "ADMIN_PASSWORD" in st.secrets:
        admin_user = st.secrets["ADMIN_USER"]
        admin_password = st.secrets["ADMIN_PASSWORD"]
    else:
        # Fallback opcional via variáveis de ambiente (útil local)
        admin_user = os.getenv("ADMIN_USER")
        admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_user or not admin_password:
        st.error(
            "Credenciais do admin não configuradas.\n\n"
            "✅ Configure em `.streamlit/secrets.toml`:\n"
            'ADMIN_USER = "seu_usuario"\n'
            'ADMIN_PASSWORD = "sua_senha"\n\n'
            "ou defina as variáveis de ambiente `ADMIN_USER` e `ADMIN_PASSWORD`."
        )
        st.stop()

    # Controle de sessão
    if "admin_logado" not in st.session_state:
        st.session_state.admin_logado = False
    if "confirmar_limpeza" not in st.session_state:
        st.session_state.confirmar_limpeza = False

    # Login
    if not st.session_state.admin_logado:
        st.subheader("Login Admin")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if usuario == admin_user and senha == admin_password:
                st.session_state.admin_logado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.stop()

    # Sidebar: logout
    if st.sidebar.button("Sair do Admin"):
        st.session_state.admin_logado = False
        st.session_state.confirmar_limpeza = False
        st.rerun()

    st.success("✅ Admin logado")

    # Ações rápidas
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Atualizar dados", use_container_width=True):
            st.rerun()

    with c2:
        if st.button("🗑️ Limpar todas as respostas", use_container_width=True):
            st.session_state.confirmar_limpeza = True

    # Confirmação de limpeza
    if st.session_state.confirmar_limpeza:
        st.warning("⚠️ Tem certeza que deseja apagar TODAS as respostas?")

        a, b = st.columns(2)
        with a:
            if st.button("✅ Sim, apagar tudo", use_container_width=True):
                if os.path.exists(FILE_PATH):
                    os.remove(FILE_PATH)
                st.session_state.confirmar_limpeza = False
                st.success("Todas as respostas foram apagadas.")
                st.rerun()

        with b:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.confirmar_limpeza = False
                st.rerun()

        st.stop()

    # Dashboard
    respostas = carregar_respostas()
    if len(respostas) == 0:
        st.info("Nenhuma resposta registrada ainda.")
        st.stop()

    df = pd.DataFrame(respostas)

    # Converte notas para número
    for c in ["clareza", "dinamica", "material"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    st.subheader("📊 Métricas Gerais")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Respostas", int(len(df)))
    m2.metric("Clareza (média)", round(df["clareza"].mean(), 2))
    m3.metric("Dinâmica (média)", round(df["dinamica"].mean(), 2))
    m4.metric("Material (média)", round(df["material"].mean(), 2))

    st.subheader("📈 Distribuição do nível da aula")
    if "nivel" in df.columns:
        st.bar_chart(df["nivel"].value_counts())

    st.subheader("💬 Sugestões dos alunos")
    sug_df = df[df.get("sugestao", "").astype(str).str.strip() != ""]
    if len(sug_df) == 0:
        st.info("Nenhuma sugestão escrita ainda.")
    else:
        # últimas sugestões primeiro
        if "timestamp" in sug_df.columns:
            try:
                sug_df = sug_df.sort_values("timestamp", ascending=False)
            except Exception:
                pass

        for _, row in sug_df.iterrows():
            when = row.get("data", "")
            texto = row.get("sugestao", "")
            st.write(f"🗨️ **{when}** — {texto}")

    st.subheader("📥 Dados completos")
    st.dataframe(df, use_container_width=True)

    st.subheader("⬇️ Exportar")
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar CSV",
        data=csv_bytes,
        file_name="respostas_pesquisa.csv",
        mime="text/csv",
        use_container_width=True,
    )

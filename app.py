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

# Admin password via secrets (preferido) ou variável de ambiente (fallback)
ADMIN_PASSWORD = None
if "ADMIN_PASSWORD" in st.secrets:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
else:
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")  # opcional

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
    out = []
    for ln in linhas:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            # Se alguma linha estiver corrompida, ignora
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
            index=1
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
            "sugestao": sugestao.strip()
        }
        salvar_resposta(resposta)
        st.success("✅ Obrigado! Sua resposta foi registrada.")


# --------------------------
# MODO ADMIN
# --------------------------
else:
    st.title("🔐 Área Administrativa")

    if not ADMIN_PASSWORD:
        st.error(
            "Senha do admin não configurada.\n\n"
            "✅ Configure em `.streamlit/secrets.toml`:\n"
            '`ADMIN_PASSWORD = "sua_senha"`\n\n'
            "ou defina a variável de ambiente `ADMIN_PASSWORD`."
        )
        st.stop()

    # Pequeno login em sessão
    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        senha = st.text_input("Digite a senha:", type="password")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            entrar = st.button("Entrar", use_container_width=True)
        with col_b:
            st.caption("Dica: use `.streamlit/secrets.toml` para não expor senha.")

        if entrar:
            if senha == ADMIN_PASSWORD:
                st.session_state.admin_ok = True
                st.success("✅ Acesso liberado.")
                st.rerun()
            else:
                st.error("Senha incorreta.")
        st.stop()

    # Botão de sair
    if st.sidebar.button("Sair do Admin"):
        st.session_state.admin_ok = False
        st.rerun()

    respostas = carregar_respostas()

    if len(respostas) == 0:
        st.warning("Nenhuma resposta registrada ainda.")
        st.stop()

    df = pd.DataFrame(respostas)

    # Normaliza colunas esperadas
    for c in ["clareza", "dinamica", "material"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    st.subheader("📊 Métricas Gerais")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Respostas", int(len(df)))
    col2.metric("Clareza (média)", round(df["clareza"].mean(), 2))
    col3.metric("Dinâmica (média)", round(df["dinamica"].mean(), 2))
    col4.metric("Material (média)", round(df["material"].mean(), 2))

    st.subheader("📈 Distribuição do nível da aula")
    if "nivel" in df.columns:
        st.bar_chart(df["nivel"].value_counts())

    st.subheader("💬 Sugestões dos alunos")
    sug_df = df[df.get("sugestao", "").astype(str).str.strip() != ""]
    if len(sug_df) == 0:
        st.info("Nenhuma sugestão escrita ainda.")
    else:
        # Mostra as últimas sugestões primeiro (se houver timestamp)
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

    # Exportação (download)
    st.subheader("⬇️ Exportar")
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar CSV",
        data=csv_bytes,
        file_name="respostas_pesquisa.csv",
        mime="text/csv",
        use_container_width=True
    )

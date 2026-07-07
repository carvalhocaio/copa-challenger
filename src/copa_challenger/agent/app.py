"""Casca Streamlit do World Cup Intelligence Desk - chat sobre o agente.

Camada fina: toda a lógica vive no agente. Aqui só há UI de chat, histórico
de mensagens e o loop de conversa. Rode com:
    uv run streamlit run src/copa_challenger/agent/app.py
"""

from __future__ import annotations

import streamlit as st

from copa_challenger.agent.agent import agent

st.set_page_config(
    page_title="World Cup Intelligence Desk",
    page_icon="⚽",
    layout="centered",
)

st.title("⚽ World Cup Intelligence Desk")
st.caption(
    "Analista de IA sobre as Copas de 2018 e 2022. "
    "Pergunte sobre seleções, eficiência de xG, pênaltis, favoritismo por ranking."
)

# histórico de mensagens na sessão (o agente é stateless; o histórico vive aqui)
if "messages" not in st.session_state:
    st.session_state.messages = []

# sugestões de partida - ajudam a banca a saber o que perguntar
with st.expander("Exemplos de perguntas"):
    st.markdown(
        "- Compare as Copas de 2018 e 2022\n"
        "- Como foi a performance da Croácia em 2022?\n"
        "- Quem mais desperdiçou chances (attack vs xG) em 2018?\n"
        "- O favorito do ranking venceu mais no mata-mata ou nos grupos?\n"
        "- Liste todas as disputas por pênaltis"
    )

# re-renderiza o histórico a cada rerun
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# input do usuário
if prompt := st.chat_input("Pergunte ao desk..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando os dados..."):
            try:
                result = agent.run_sync(prompt)
                answer = result.output
            except Exception as e:  # ambiente sem chave, erro de rede etc.
                answer = f"Não consegui responder agora: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

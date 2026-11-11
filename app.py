"""
app.py — same agent, wrapped in a Streamlit web UI.

    streamlit run app.py

Streamlit reruns this whole script on every interaction; st.session_state
is how the agent (and its message memory) survives between reruns.
"""
import streamlit as st
from agent import Agent

st.set_page_config(page_title="Forge — mini AI agent", page_icon="🛠")
st.title("Forge — a from-scratch AI agent")
st.caption("Claude + a Python while-loop + 4 tools. That's the whole trick.")

if "agent" not in st.session_state:
    try:
        st.session_state.agent = Agent()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()
    st.session_state.log = []  # display log: (role, text)

for role, text in st.session_state.log:
    st.chat_message(role).write(text)

if prompt := st.chat_input("Ask the agent to do something..."):
    st.session_state.log.append(("user", prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        def show(kind, data):
            if kind == "tool_call":
                name, inputs = data
                st.markdown(f"`>> {name}({inputs})`")
            elif kind == "tool_result":
                st.code(data[:1000])
            elif kind == "text":
                st.write(data)
                st.session_state.log.append(("assistant", data))

        try:
            st.session_state.agent.run(prompt, on_event=show)
        except Exception as e:
            st.error(f"Agent error: {e}")

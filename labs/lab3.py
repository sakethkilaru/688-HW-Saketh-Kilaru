import streamlit as st
from openai import OpenAI

st.title("Chatbot")

#secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
if "messages" not in st.session_state:
    st.session_state.messages = []

#save messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#input
if prompt := st.chat_input("What is up?"):
    #user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # reply
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        response = st.write_stream(stream)

    # add to message history
    st.session_state.messages.append({"role": "assistant", "content": response})
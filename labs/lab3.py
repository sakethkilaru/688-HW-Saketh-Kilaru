import streamlit as st
from openai import OpenAI

st.title("Chatbot")

# secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
if "messages" not in st.session_state:
    st.session_state.messages = []

# display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# input
if prompt := st.chat_input("What is up?"):
    # user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # keep only last 2 user messages 
    user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
    if len(user_msgs) > 2:
        # find index of the 2nd-to-last user message
        cutoff_index = len(st.session_state.messages) - 1
        count = 0
        for i in range(len(st.session_state.messages) - 1, -1, -1):
            if st.session_state.messages[i]["role"] == "user":
                count += 1
            if count == 2:
                cutoff_index = i
                break
        # truncate messages before cutoff_index
        st.session_state.messages = st.session_state.messages[cutoff_index:]

    # reply
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]}
                      for m in st.session_state.messages],
            stream=True,
        )
        response = st.write_stream(stream)

    # add assistant reply
    st.session_state.messages.append({"role": "assistant", "content": response})

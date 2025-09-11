import streamlit as st
from openai import OpenAI

st.title("Chatbot")

# secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# System prompt
SYSTEM_PROMPT = """From now on follow this: Take my user input and always reply with "DO YOU WANT MORE INFO" at the end of it. If I say yes, give me more info and then say "DO YOU WANT MORE INFO" indefinitely till I say no. If I say no, wait for my prompt to ask you what I need. And explain everything like you're talking to someone who's 10 years old."""

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
    
    # keep only last 20 user messages 
    user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
    if len(user_msgs) > 20:
        # find index of the 2nd-to-last user message
        cutoff_index = len(st.session_state.messages) - 1
        count = 0
        for i in range(len(st.session_state.messages) - 1, -1, -1):
            if st.session_state.messages[i]["role"] == "user":
                count += 1
            if count == 2:
                cutoff_index = i
                break
        st.session_state.messages = st.session_state.messages[cutoff_index:]
    
    # reply
    with st.chat_message("assistant"):
        # Create messages list with system prompt at the beginning
        messages_with_system = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": m["role"], "content": m["content"]} 
            for m in st.session_state.messages
        ]
        
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=messages_with_system,
            stream=True,
        )
        response = st.write_stream(stream)
    
    # add assistant reply
    st.session_state.messages.append({"role": "assistant", "content": response})
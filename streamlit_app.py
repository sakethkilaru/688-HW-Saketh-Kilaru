import streamlit as st

# Multi-page navigation (HW Manager)
pg = st.navigation(
    {
        "HW Manager": [
            st.Page("labs/lab1.py", title="Document Q&A", icon="📄"),
            st.Page("labs/lab3.py", title="Chatbot", icon="🤖"),
            st.Page("labs/lab4.py", title="Embedding", icon="⚙️"),

        ],
    }
)

pg.run()

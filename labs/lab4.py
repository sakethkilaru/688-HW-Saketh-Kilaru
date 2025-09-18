# --- Fix for sqlite3 in Streamlit with ChromaDB ---
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from openai import OpenAI
import chromadb
import fitz  # PyMuPDF

# ---- Lab 4B ----
st.title("Lab 4B – Course Information Chatbot (RAG)")

# Initialize OpenAI client once
if "openai_client" not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.openai_client = OpenAI(api_key=api_key)

# Path for persistent ChromaDB (per run)
CHROMA_DB_PATH = "./ChromaDB_for_lab4"

def extract_text_from_pdf(uploaded_file):
    """Extract all text from a PDF file using PyMuPDF."""
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text("text")
    return text


def create_lab4_vectordb(uploaded_files):
    """Create and store Lab4 ChromaDB collection in session state."""
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection("Lab4Collection")

    openai_client = st.session_state.openai_client

    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith(".pdf"):
            # Extract text
            text = extract_text_from_pdf(uploaded_file)

            if text.strip():
                # Generate embedding
                response = openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                embedding = response.data[0].embedding

                # Add to ChromaDB
                collection.add(
                    documents=[text],
                    ids=[uploaded_file.name],
                    embeddings=[embedding],
                    metadatas=[{"filename": uploaded_file.name}]
                )

    # Store in session_state
    st.session_state.Lab4_vectorDB = collection
    return collection


# ---- File uploader ----
uploaded_files = st.file_uploader(
    "Upload your 7 course PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    if "Lab4_vectorDB" not in st.session_state:
        st.write("⚡ Creating ChromaDB collection from uploaded PDFs…")
        collection = create_lab4_vectordb(uploaded_files)
    else:
        collection = st.session_state.Lab4_vectorDB
        st.write("Using cached ChromaDB collection")

    # ---- Conversational Chatbot ----
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask me something about the course..."):
        # Add user msg
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # ---- Step 1: Embed query & search ChromaDB ----
        openai_client = st.session_state.openai_client
        response = openai_client.embeddings.create(
            input=prompt,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        results = collection.query(query_embeddings=[query_embedding], n_results=3)

        # Retrieved documents
        retrieved_docs = results["documents"][0]
        retrieved_ids = results["ids"][0]

        # Build context for LLM
        context_text = "\n\n".join(
            [f"From {doc_id}:\n{doc[:1000]}"  # truncate to avoid token overflow
             for doc, doc_id in zip(retrieved_docs, retrieved_ids)]
        )

        # ---- Step 2: Build system prompt for RAG ----
        system_prompt = f"""
        You are a helpful Course Information Assistant.
        Always check the retrieved course documents for answers.
        If relevant context is found, use it and say:
        "According to the course materials..."
        If nothing relevant is found, clearly say:
        "I could not find this in the uploaded materials, but here is what I know..."
        
        Retrieved context:
        {context_text}
        """

        # ---- Step 3: Call LLM ----
        with st.chat_message("assistant"):
            messages_with_context = [
                {"role": "system", "content": system_prompt},
                *st.session_state.messages
            ]
            stream = openai_client.chat.completions.create(
                model="gpt-5-nano",  
                messages=messages_with_context,
                stream=True,
            )
            response_text = st.write_stream(stream)

        # Save assistant reply
        st.session_state.messages.append({"role": "assistant", "content": response_text})

else:
    st.info("Please upload your 7 PDF files to build the course knowledge base.")

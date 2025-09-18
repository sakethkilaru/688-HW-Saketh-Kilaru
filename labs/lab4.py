# --- Fix for sqlite3 in Streamlit with ChromaDB ---
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from openai import OpenAI
import chromadb
import fitz  # PyMuPDF

# ---- Lab 4A ----
st.title("Lab 4A – ChromaDB with OpenAI Embeddings (Upload PDFs)")

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
    "Upload your 7 PDF files",
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

    # ---- Test queries ----
    test_queries = ["Generative AI", "Text Mining", "Data Science Overview"]
    st.subheader("Test Queries")

    openai_client = st.session_state.openai_client
    for query in test_queries:
        response = openai_client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        results = collection.query(query_embeddings=[query_embedding], n_results=3)

        st.write(f"### Results for: `{query}`")
        for i, doc_id in enumerate(results["ids"][0]):
            st.write(f"{i+1}. {doc_id}")
        st.markdown("---")
else:
    st.info("upload your 7 PDF files to build the vector database.")

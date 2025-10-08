import os
import re
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer, util

# ==========================
# Helper Functions
# ==========================

def extract_text_from_pdf(uploaded_files):
    """Extracts text from uploaded PDF resumes"""
    resumes_data = []
    for file in uploaded_files:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

        name = os.path.splitext(file.name)[0]
        skills = extract_skills(text)
        experience = extract_experience(text)

        resumes_data.append({
            "Name": name,
            "Text": text,
            "Skills": ", ".join(skills) if skills else "Not Mentioned",
            "Experience": experience
        })
    return pd.DataFrame(resumes_data)


def extract_skills(text):
    """Extracts skills from text using keyword matching"""
    skill_keywords = [
        "python", "sql", "excel", "tableau", "power bi", "machine learning",
        "deep learning", "nlp", "pandas", "numpy", "scikit-learn", "aws", "java", "c++", "django"
    ]
    found = [skill for skill in skill_keywords if re.search(rf"\b{skill}\b", text.lower())]
    return found


def extract_experience(text):
    """Extracts years of experience using regex"""
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience", text.lower())
    if exp_match:
        return exp_match.group(1) + " years"
    else:
        return "Not Mentioned"


def create_vector_store(df):
    """Creates a FAISS vector store from resumes"""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    texts = []
    metadatas = []
    for _, row in df.iterrows():
        text = f"Name: {row['Name']}\nSkills: {row['Skills']}\nExperience: {row['Experience']}\nResume: {row['Text']}"
        texts.append(text)
        metadatas.append({"Name": row['Name'], "Skills": row['Skills'], "Experience": row['Experience']})

    vector_db = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    return vector_db, model


def search_candidates(query, vector_db, model, top_k=3):
    """Finds best-matching resumes based on query"""
    query_embedding = model.encode(query, convert_to_tensor=True)
    results = vector_db.similarity_search(query, k=top_k)
    return results


# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Resume Screening Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Resume Screening Chatbot")
st.markdown("Upload resumes and ask queries like: *Suggest me SQL developers with 3+ years of experience*")

# Upload resumes
uploaded_files = st.file_uploader("📂 Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing resumes..."):
        resumes_df = extract_text_from_pdf(uploaded_files)
        vector_db, model = create_vector_store(resumes_df)
        st.success("✅ Resumes uploaded and processed successfully!")

    st.dataframe(resumes_df[["Name", "Skills", "Experience"]])

    query = st.text_input("💬 Enter your query:")
    if query:
        with st.spinner("Searching best candidates..."):
            results = search_candidates(query, vector_db, model)

        st.subheader("🎯 Recommended Candidates:")
        for res in results:
            st.write(f"**Name:** {res.metadata['Name']}")
            st.write(f"**Skills:** {res.metadata['Skills']}")
            st.write(f"**Experience:** {res.metadata['Experience']}")
            st.write("---")
else:
    st.info("👆 Upload PDF resumes to get started.")

st.divider()
st.caption("Developed by Sai Santhosh | Powered by RAG | © 2025")
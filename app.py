import os
import re
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ==========================
# Helper Functions
# ==========================

def extract_text_from_pdf(uploaded_files):
    resumes_data = []
    for file in uploaded_files:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

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
    skill_keywords = [
        "python", "sql", "excel", "tableau", "power bi", "machine learning",
        "deep learning", "nlp", "pandas", "numpy", "scikit-learn",
        "aws", "java", "c++", "django"
    ]
    found = [skill for skill in skill_keywords if re.search(rf"\b{skill}\b", text.lower())]
    return found


def extract_experience(text):
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience", text.lower())
    if exp_match:
        return exp_match.group(1) + " years"
    else:
        return "Not Mentioned"


def embed_texts(texts):
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

    embeddings = []
    for text in texts:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            embeddings.append(emb)
    return np.vstack(embeddings)


def search_candidates(query, resumes_df, embeddings):
    query_emb = embed_texts([query])[0]
    cos_sim = cosine_similarity([query_emb], embeddings)[0]
    top_idx = cos_sim.argsort()[-3:][::-1]
    results = []
    for idx in top_idx:
        row = resumes_df.iloc[idx]
        results.append({
            "Name": row["Name"],
            "Skills": row["Skills"],
            "Experience": row["Experience"]
        })
    return results

# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Resume Screening Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Resume Screening Chatbot")
st.markdown("""
Upload multiple PDF resumes and query like:  
**_“Suggest me SQL developers with 3+ years of experience.”_**
""")

uploaded_files = st.file_uploader("📂 Upload Resumes (PDF format)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing resumes..."):
        resumes_df = extract_text_from_pdf(uploaded_files)
        embeddings = embed_texts(resumes_df['Text'].tolist())
        st.success("✅ Resumes uploaded and processed successfully!")

    st.dataframe(resumes_df[["Name", "Skills", "Experience"]])

    query = st.text_input("💬 Enter your query:")
    if query:
        with st.spinner("Searching for the best candidates..."):
            results = search_candidates(query, resumes_df, embeddings)

        st.subheader("🎯 Recommended Candidates:")
        if results:
            for res in results:
                st.markdown(f"""
                **👤 Name:** {res['Name']}  
                **🧠 Skills:** {res['Skills']}  
                **💼 Experience:** {res['Experience']}  
                ---  
                """)
        else:
            st.warning("No matching candidates found for your query.")
else:
    st.info("👆 Upload PDF resumes to get started.")

st.divider()
st.caption("Developed by Sai Santhosh | Powered by RAG | © 2025")

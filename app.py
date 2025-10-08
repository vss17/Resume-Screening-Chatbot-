import os
import re
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util

# ==========================
# Helper Functions
# ==========================

def extract_text_from_pdf(uploaded_files):
    """Extract text and key info from uploaded PDF resumes"""
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
    """Extracts skills from text using simple keyword matching"""
    skill_keywords = [
        "python", "sql", "excel", "tableau", "power bi", "machine learning",
        "deep learning", "nlp", "pandas", "numpy", "scikit-learn",
        "aws", "java", "c++", "django"
    ]
    found = [skill for skill in skill_keywords if re.search(rf"\b{skill}\b", text.lower())]
    return found


def extract_experience(text):
    """Extracts years of experience using regex patterns"""
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience", text.lower())
    if exp_match:
        return exp_match.group(1) + " years"
    else:
        return "Not Mentioned"


def embed_resumes(resumes_df):
    """Generate embeddings for all resumes"""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = [model.encode(text, convert_to_tensor=True) for text in resumes_df['Text']]
    return model, embeddings


def search_candidates(query, resumes_df, embeddings, model, top_k=3):
    """Find best-matching resumes based on query"""
    query_emb = model.encode(query, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_emb, embeddings)[0]
    top_results = cos_scores.topk(k=top_k)
    results = []
    for idx in top_results.indices:
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

# Upload resumes
uploaded_files = st.file_uploader("📂 Upload Resumes (PDF format)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing resumes..."):
        resumes_df = extract_text_from_pdf(uploaded_files)
        model, embeddings = embed_resumes(resumes_df)
        st.success("✅ Resumes uploaded and processed successfully!")

    st.dataframe(resumes_df[["Name", "Skills", "Experience"]])

    # Query Section
    query = st.text_input("💬 Enter your query:")
    if query:
        with st.spinner("Searching for the best candidates..."):
            results = search_candidates(query, resumes_df, embeddings, model)

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

# Footer
st.divider()
st.caption("Developed by **Sai Santhosh** | Powered by **Local RAG (Sentence-Transformers)** | © 2025")

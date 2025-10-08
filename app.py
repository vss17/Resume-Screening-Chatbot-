import os
import re
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader

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

def search_candidates(query, df):
    """Search resumes based on keyword matches in skills and experience"""
    query_keywords = query.lower().split()
    results = []
    for _, row in df.iterrows():
        text = f"{row['Skills']} {row['Experience']}".lower()
        if all(k in text for k in query_keywords):
            results.append({
                "Name": row["Name"],
                "Skills": row["Skills"],
                "Experience": row["Experience"]
            })
    return results[:5]  # top 5 matches

# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Resume Screening Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Resume Screening Chatbot")
st.markdown("Upload PDF resumes and search candidates by keywords in skills or experience.")

uploaded_files = st.file_uploader("📂 Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing resumes..."):
        resumes_df = extract_text_from_pdf(uploaded_files)
        st.success("✅ Resumes processed successfully!")

    st.dataframe(resumes_df[["Name", "Skills", "Experience"]])

    query = st.text_input("💬 Enter your query (e.g., 'SQL 3 years'):")
    if query:
        with st.spinner("Searching for matching candidates..."):
            results = search_candidates(query, resumes_df)

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
            st.warning("No matching candidates found.")
else:
    st.info("👆 Upload PDF resumes to get started.")

st.divider()
st.caption("Developed by Sai Santhosh | Powered by Keyword Search | © 2025")

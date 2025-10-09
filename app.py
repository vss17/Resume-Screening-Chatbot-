import os
import re
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader

# ================= Helper Functions =================
def extract_text_from_pdf(file):
    text = ""
    pdf = PdfReader(file)
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

def extract_skills(text):
    keywords = ["python", "sql", "excel", "tableau", "power bi", "ml", "deep learning",
                "nlp", "pandas", "numpy", "scikit-learn", "java", "c++", "django"]
    return [k for k in keywords if k.lower() in text.lower()]

def extract_experience(text):
    match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text.lower())
    return match.group(1) + " years" if match else "Not Mentioned"

def process_resumes(uploaded_files=None, folder_path=None):
    data = []
    files = []
    if uploaded_files:
        files = uploaded_files
    elif folder_path and os.path.isdir(folder_path):
        pdfs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".pdf")]
        files = [open(p, "rb") for p in pdfs]
    for file in files:
        text = extract_text_from_pdf(file)
        name = os.path.splitext(os.path.basename(getattr(file, "name", "unknown.pdf")))[0]
        skills = extract_skills(text)
        exp = extract_experience(text)
        data.append({
            "Name": name,
            "Skills": ", ".join(skills) if skills else "Not Mentioned",
            "Experience": exp
        })
    return pd.DataFrame(data)

def search_candidates(df, query):
    query_skills = re.findall(r'\b\w+\b', query.lower())
    exp_match = re.search(r'(\d+)\+?', query)
    min_exp = int(exp_match.group(1)) if exp_match else 0
    results = []
    for _, row in df.iterrows():
        candidate_skills = [s.lower() for s in row['Skills'].split(", ")]
        candidate_exp = 0 if row['Experience'] == "Not Mentioned" else int(re.search(r'\d+', row['Experience']).group())
        if any(q in candidate_skills for q in query_skills) and candidate_exp >= min_exp:
            results.append(row)
    return pd.DataFrame(results)

# ================= Streamlit UI =================
st.set_page_config(page_title="Resume Screening Chatbot", page_icon="🤖", layout="centered")

# ===== Custom CSS =====
st.markdown("""
    <style>
    body {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
        color: white;
    }
    div[data-testid="stAppViewContainer"] {
        background: transparent;
        padding-top: 0 !important;
        margin-top: -50px !important;
    }
    .main-card {
        background: rgba(25, 35, 45, 0.9);
        backdrop-filter: blur(8px);
        border-radius: 15px;
        padding: 35px;
        max-width: 700px;
        margin: 0 auto;
        box-shadow: 0 4px 25px rgba(0,0,0,0.3);
        text-align: center;
    }
    h1 {
        color: #00FFB2;
        text-align: center;
        font-size: 2rem;
        margin-top: 0px !important;
        margin-bottom: 8px;
    }
    .subtitle {
        color: #B0BEC5;
        font-style: italic;
        text-align: center;
        margin-bottom: 20px;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        height: 45px;
    }
    .stButton>button {
        background-color: #00FFB2;
        color: black;
        border: none;
        border-radius: 8px;
        height: 45px;
        width: 100%;
        font-weight: bold;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #00e5a0;
    }
    </style>
""", unsafe_allow_html=True)

# ===== App Title =====
st.markdown("<h1>🤖 Resume Screening Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Try: <b>Suggest me SQL developers with 3+ years of experience</b></p>", unsafe_allow_html=True)

# ===== Main UI Card =====
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

option = st.radio("Choose Input Method:", ["📤 Upload Resumes", "📁 Use Folder Path"], horizontal=True)

uploaded_files, folder_path = None, None
if option == "📤 Upload Resumes":
    uploaded_files = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True)
elif option == "📁 Use Folder Path":
    folder_path = st.text_input("Enter folder path containing PDFs")

# Process resumes
resumes_df = None
if st.button("Process Resumes"):
    if uploaded_files or (folder_path and os.path.isdir(folder_path)):
        resumes_df = process_resumes(uploaded_files=uploaded_files, folder_path=folder_path)
        st.success(f"✅ {len(resumes_df)} resumes processed successfully!")
    else:
        st.warning("Please upload resumes or provide a valid folder path.")

# Query
query = st.text_input("💬 Enter your query", placeholder="e.g. Python developer with 2+ years experience")

if query and resumes_df is not None:
    results = search_candidates(resumes_df, query)
    if not results.empty:
        st.markdown("### 🧩 Matching Candidates")
        st.dataframe(results, use_container_width=True)
    else:
        st.warning("No matching candidates found.")
elif query:
    st.info("📂 Please process resumes first.")

st.markdown("<p style='margin-top:30px; color:#90A4AE; font-size:13px;'>Developed by Sai Santhosh | © 2025</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

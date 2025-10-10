import os
import streamlit as st
from PyPDF2 import PdfReader
import re

# --------------------------- #
# Utility Functions
# --------------------------- #

def extract_text_from_pdf(pdf_path):
    """Extract text from a single PDF file."""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            text = "\n".join(
                [page.extract_text() for page in reader.pages if page.extract_text()]
            )
            return text.strip()
    except Exception as e:
        st.error(f"Error reading {pdf_path}: {e}")
        return ""


def load_resumes_from_path(path):
    """Load PDF resumes from a given file or folder path."""
    path = path.strip().strip('"').replace("\\", "/")

    if os.path.isfile(path) and path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(path)
        if text:
            return [{"name": os.path.basename(path), "text": text}]
        return []

    elif os.path.isdir(path):
        pdf_files = [
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.lower().endswith(".pdf")
        ]
        resumes = []
        for pdf in pdf_files:
            text = extract_text_from_pdf(pdf)
            if text:
                resumes.append({"name": os.path.basename(pdf), "text": text})
        return resumes

    else:
        return []


def load_uploaded_resumes(uploaded_files):
    """Load resumes from uploaded PDF files."""
    resumes = []
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            text = "\n".join(
                [page.extract_text() for page in reader.pages if page.extract_text()]
            )
            if text:
                resumes.append({"name": uploaded_file.name, "text": text})
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")
    return resumes


def search_resumes(resumes, query):
    """Simple keyword-based search."""
    query_words = query.lower().split()
    results = []

    for resume in resumes:
        text = resume["text"].lower()
        if all(word in text for word in query_words):
            # Try to extract years of experience
            exp_match = re.search(r"(\d+)\+?\s*year", text)
            exp = exp_match.group(1) + " years" if exp_match else "Not specified"
            results.append(
                {
                    "name": resume["name"],
                    "experience": exp,
                    "snippet": " ".join(resume["text"].split()[:50]) + "...",
                }
            )
    return results


# --------------------------- #
# Streamlit App UI
# --------------------------- #

st.set_page_config(page_title="Resume Screening Chatbot", layout="centered")

st.markdown(
    """
    <style>
    body {
        background-color: #0e1117;
        color: #f1f1f1;
        font-family: 'Segoe UI', sans-serif;
    }
    .stTextInput>div>div>input {
        background-color: #2c303b;
        color: #fff;
    }
    .stButton>button {
        background-color: #00FFBF;
        color: black;
        border-radius: 10px;
        font-weight: bold;
    }
    h1 {
        text-align: center;
        color: #00FFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------- #
# Title and Input Section
# --------------------------- #

st.markdown("<h1>💼 Resume Screening Chatbot</h1>", unsafe_allow_html=True)

input_method = st.radio(
    "Choose input method:",
    ["📤 Upload Resumes (PDFs)", "📁 Provide Local Path (file or folder)"],
    horizontal=True,
)

resumes = []

if input_method == "📤 Upload Resumes (PDFs)":
    uploaded_files = st.file_uploader("Upload one or more PDF resumes", type=["pdf"], accept_multiple_files=True)
    if st.button("Process Resumes"):
        if uploaded_files:
            resumes = load_uploaded_resumes(uploaded_files)
            st.success(f"✅ {len(resumes)} resumes processed successfully.")
        else:
            st.error("Please upload at least one PDF file.")

else:
    path_input = st.text_input("Enter a local full path to a folder or single PDF file")
    if st.button("Process Resumes"):
        if path_input.strip():
            resumes = load_resumes_from_path(path_input)
            if resumes:
                st.success(f"✅ {len(resumes)} resumes processed successfully.")
            else:
                st.error("No valid PDF files found at that path. Make sure path is correct and contains .pdf files.")
        else:
            st.warning("Please enter a valid path.")

st.divider()

if not resumes:
    st.info("No resumes processed yet.")
else:
    query = st.text_input("💬 Enter your query (e.g., 'SQL developers with 3+ years')")
    if st.button("Search"):
        if query.strip():
            results = search_resumes(resumes, query)
            if results:
                st.subheader("🔍 Matching Candidates:")
                for r in results:
                    st.markdown(
                        f"""
                        **🧑 Name:** {r['name']}  
                        **💼 Experience:** {r['experience']}  
                        **📝 Snippet:** {r['snippet']}  
                        ---
                        """
                    )
            else:
                st.warning("No matching candidates found.")
        else:
            st.warning("Please enter a query to search.")

st.markdown("<br><center>Developed by <b>Sai Santhosh</b> © 2025</center>", unsafe_allow_html=True)

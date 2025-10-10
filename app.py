import os
import re
import io
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader

# -----------------------
# Helper functions
# -----------------------
def read_pdf_from_bytes(bytes_obj):
    """Return text extracted from a bytes-like PDF (UploadedFile.read())."""
    try:
        reader = PdfReader(io.BytesIO(bytes_obj))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception:
        return ""

def read_pdf_from_path(path):
    """Return text extracted from a PDF file path."""
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except Exception:
        return ""

def extract_skills(text):
    keywords = [
        "python", "sql", "excel", "tableau", "power bi", "powerbi", "power-bi",
        "machine learning", "deep learning", "nlp", "pandas", "numpy",
        "scikit-learn", "aws", "azure", "gcp", "java", "c++", "c#", "django",
        "flask", "docker", "kubernetes", "spark", "hadoop", "git", "react",
        "javascript"
    ]
    t = text.lower()
    found = [k for k in keywords if re.search(rf"\b{re.escape(k)}\b", t)]
    # normalize some names
    normalized = []
    for s in sorted(set(found)):
        if s in ("powerbi", "power-bi"):
            normalized.append("Power BI")
        elif s in ("scikit-learn", "scikit", "sklearn"):
            normalized.append("scikit-learn")
        else:
            normalized.append(s.title())
    return normalized

def extract_experience_years(text):
    t = text.lower()
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\b",
        r"over\s+(\d+)\s*(?:years?|yrs?)\b",
        r"(\d+)\s*-\s*(\d+)\s*years"
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                continue
    # words to numbers (small set)
    words = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7}
    for w, n in words.items():
        if re.search(rf"\b{w}\b\s*(?:years?|yrs?)", t):
            return n
    return 0

def process_from_uploaded(uploaded_files):
    rows = []
    for f in uploaded_files:
        try:
            bytes_pdf = f.read()
            text = read_pdf_from_bytes(bytes_pdf)
        except Exception:
            text = ""
        name = os.path.splitext(f.name)[0]
        skills = extract_skills(text)
        exp = extract_experience_years(text)
        rows.append({
            "Name": name,
            "Skills": ", ".join(skills) if skills else "Not Mentioned",
            "ExperienceYears": exp,
            "TextPreview": (text[:1000] + "...") if text else ""
        })
    return pd.DataFrame(rows)

def process_from_path(path_input):
    """
    Accepts:
     - folder path containing PDFs
     - single PDF file path
    Returns DataFrame or None if invalid.
    """
    rows = []
    if os.path.isdir(path_input):
        pdfs = [p for p in os.listdir(path_input) if p.lower().endswith(".pdf")]
        if not pdfs:
            return None
        for pdf in pdfs:
            full = os.path.join(path_input, pdf)
            text = read_pdf_from_path(full)
            name = os.path.splitext(pdf)[0]
            skills = extract_skills(text)
            exp = extract_experience_years(text)
            rows.append({
                "Name": name,
                "Skills": ", ".join(skills) if skills else "Not Mentioned",
                "ExperienceYears": exp,
                "TextPreview": (text[:1000] + "...") if text else ""
            })
        return pd.DataFrame(rows)
    elif os.path.isfile(path_input) and path_input.lower().endswith(".pdf"):
        text = read_pdf_from_path(path_input)
        name = os.path.splitext(os.path.basename(path_input))[0]
        skills = extract_skills(text)
        exp = extract_experience_years(text)
        rows.append({
            "Name": name,
            "Skills": ", ".join(skills) if skills else "Not Mentioned",
            "ExperienceYears": exp,
            "TextPreview": (text[:1000] + "...") if text else ""
        })
        return pd.DataFrame(rows)
    else:
        return None

def search_candidates(df, query):
    # find numeric experience in query (e.g., 3+ years)
    exp_match = re.search(r"(\d+)\+?", query)
    min_exp = int(exp_match.group(1)) if exp_match else 0
    # find keywords (words of length >=2)
    tokens = [t for t in re.findall(r"\b[a-zA-Z\+#]+\b", query.lower()) if len(t) > 1]
    results = []
    for _, row in df.iterrows():
        candidate_skills = [s.strip().lower() for s in row["Skills"].split(",")] if row["Skills"] != "Not Mentioned" else []
        candidate_exp = int(row["ExperienceYears"]) if row["ExperienceYears"] else 0
        skill_match = any(tok.lower() in candidate_skills or tok.lower() in row["Name"].lower() for tok in tokens)
        if (not tokens or skill_match) and candidate_exp >= min_exp:
            results.append(row)
    if results:
        return pd.DataFrame(results)
    else:
        return pd.DataFrame(columns=df.columns)

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Resume Screening Chatbot", page_icon="🤖", layout="centered")

# CSS: remove top spacing and style card
st.markdown(
    """
    <style>
    body {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
        color: #e6eef0;
    }
    div[data-testid="stAppViewContainer"] {
        padding-top: 2px !important;
        margin-top: 0px !important;
    }
    .card {
        max-width: 760px;
        margin: 10px auto 60px auto;
        padding: 32px;
        background: rgba(18, 28, 36, 0.9);
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.45);
    }
    h1 { color:#00FFB2; margin:0 0 6px 0; }
    .subtitle { color: #a8bcc2; margin-bottom: 18px; font-style: italic; }
    .stButton>button { background-color: #00FFB2; color: black; border-radius:8px; height:44px; font-weight:600; }
    .stButton>button:hover{ background-color:#00e5a0; }
    .small-muted { color: #9fb0b6; font-size:13px; margin-top:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<h1>🤖 Resume Screening Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Try queries like: <b>Suggest me SQL developers with 3+ years of experience</b></div>", unsafe_allow_html=True)

# Input selection
input_method = st.radio("Choose input method:", ("Upload Resumes (PDFs)", "Provide Local Path (file or folder)"), horizontal=True)

uploaded_files = None
path_input = ""

if input_method == "Upload Resumes (PDFs)":
    uploaded_files = st.file_uploader("Upload PDF resumes (you may upload multiple)", type=["pdf"], accept_multiple_files=True)
else:
    path_input = st.text_input("Enter a local full path to a folder or single PDF file", placeholder=r"C:\Users\MYPC\Downloads  OR  C:\Users\MYPC\Downloads\John Doe.pdf")

# Process button
resumes_df = None
if st.button("Process Resumes"):
    if input_method == "Upload Resumes (PDFs)":
        if not uploaded_files:
            st.warning("Please upload one or more PDF files first.")
        else:
            with st.spinner("Processing uploaded resumes..."):
                resumes_df = process_from_uploaded(uploaded_files)
                if resumes_df is None or resumes_df.empty:
                    st.error("No text could be extracted from uploaded files.")
                else:
                    st.success(f"Processed {len(resumes_df)} resume(s).")
    else:
        if not path_input:
            st.warning("Please enter a local path (folder or single PDF file).")
        else:
            path_input_stripped = path_input.strip().strip('"')
            with st.spinner("Processing path..."):
                resumes_df = process_from_path(path_input_stripped)
                if resumes_df is None or resumes_df.empty:
                    st.error("No valid PDF files found at that path. Make sure path is correct and contains .pdf files.")
                else:
                    st.success(f"Processed {len(resumes_df)} resume(s) from path.")

# Show preview table if available
if 'resumes_df' in locals() and resumes_df is not None and not resumes_df.empty:
    st.markdown("### 📄 Resumes Preview")
    st.dataframe(resumes_df[["Name", "Skills", "ExperienceYears"]].rename(columns={"ExperienceYears":"Experience (Years)"}), use_container_width=True)
    st.markdown("<div class='small-muted'>Tip: After processing resumes, enter a query below to find matching candidates.</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='small-muted'>No resumes processed yet.</div>", unsafe_allow_html=True)

st.markdown("---")

# Query and search
query = st.text_input("💬 Enter your query (e.g., 'SQL developers with 3+ years')")

if st.button("Search"):
    if 'resumes_df' not in locals() or resumes_df is None or resumes_df.empty:
        st.info("Please process resumes first (upload or provide a valid local path).")
    elif not query or query.strip() == "":
        st.warning("Please type a query.")
    else:
        results = search_candidates(resumes_df, query)
        if results is None or results.empty:
            st.warning("No matching candidates found.")
        else:
            st.success(f"Found {len(results)} matching candidate(s).")
            # show neat table (Name, Skills, Experience)
            display = results[["Name", "Skills", "ExperienceYears"]].rename(columns={"ExperienceYears":"Experience (Years)"})
            st.dataframe(display, use_container_width=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("<div style='color:#90A4AE; font-size:13px;'>Developed by Sai Santhosh | © 2025</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

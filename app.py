import streamlit as st
from streamlit_lottie import st_lottie
import json
import fitz  # PyMuPDF
import tempfile
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Lottie Animation
def load_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_scanner = load_lottie("scanner.json")

# Streamlit Page Config
st.set_page_config(page_title="Insurance Policy Extractor", layout="wide")

# Custom Styling
st.markdown("""
    <style>
        .main {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        .hero {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(90deg, #00ffcc, #0066ff);
            color: white;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .card {
            background-color: #161b22;
            border-radius: 12px;
            padding: 15px;
            margin: 10px;
            box-shadow: 0 0 10px #00ffcc;
        }
    </style>
""", unsafe_allow_html=True)

<<<<<<< HEAD
# Hero Section
st.markdown("""
    <div class="hero">
        <h1>📄 Insurance Policy Extractor</h1>
        <p>Upload your PDF(s) and get structured, AI-generated policy details.</p>
    </div>
""", unsafe_allow_html=True)
=======
    Format the output as JSON with keys:
    customer name, policy_number, start_date, end_date, sum_insured, insurance_type, od_amount, tp_amount
>>>>>>> 125058b2a9ffd0800088d66b78e86dc732e5f32d

st_lottie(lottie_scanner, height=200)

# PDF to Text Extraction
def extract_text_from_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# AI Policy Info Extraction
def extract_policy_fields(text):
    prompt = f"""
Extract the following fields from the insurance policy text:
- Policy Number
- Policy Start Date
- Policy End Date
- SP Code
- Customer Name
- Gross Amount
- Net Amount
- Sum Insured
- TP Amount (if motor policy, else 0)
- OD Amount (if motor policy, else 0)

Return this format:
Policy Number:  
Start Date:  
End Date:  
SP Code:  
Customer Name:  
Gross Amount:  
Net Amount:  
Sum Insured:  
TP Amount:  
OD Amount:  
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt + "\n\nPolicy Text:\n" + text}],
        temperature=0
    )
    return response.choices[0].message.content

# Choose Upload Mode
upload_mode = st.radio("Select Upload Mode", ["Single PDF", "Multiple PDFs"], horizontal=True)

# DataFrame for CSV Export
df_output = pd.DataFrame()

if upload_mode == "Single PDF":
    uploaded_file = st.file_uploader("Upload a Policy PDF", type=["pdf"])
    if uploaded_file:
        st.success("✅ File uploaded. Extracting...")
        text = extract_text_from_pdf(uploaded_file)
        result = extract_policy_fields(text)

        # Display results
        fields = dict(line.split(":", 1) for line in result.split("\n") if ":" in line)

        for key, value in fields.items():
            if key.strip() in ["TP Amount", "OD Amount"] and value.strip() == "0":
                continue  # Hide for non-motor policies
            st.markdown(f"<div class='card'><strong>{key}:</strong> {value}</div>", unsafe_allow_html=True)

        # Prepare CSV row
        df_output = pd.DataFrame([fields])

else:
    uploaded_files = st.file_uploader("Upload Multiple PDFs", type=["pdf"], accept_multiple_files=True)
    all_rows = []
    if uploaded_files:
        for file in uploaded_files:
            st.write(f"Processing: {file.name}")
            text = extract_text_from_pdf(file)
            result = extract_policy_fields(text)
            fields = dict(line.split(":", 1) for line in result.split("\n") if ":" in line)
            all_rows.append(fields)
        df_output = pd.DataFrame(all_rows)
        st.dataframe(df_output)

# CSV Download
if not df_output.empty:
    csv = df_output.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Extracted Data as CSV",
        data=csv,
        file_name='extracted_policy_data.csv',
        mime='text/csv'
    )

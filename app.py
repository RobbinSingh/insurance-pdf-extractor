import streamlit as st
import fitz  # PyMuPDF
import tempfile
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Styling ---
st.set_page_config(page_title="Insurance Policy Extractor", layout="wide")
st.markdown("""
    <style>
        .hero {
            text-align: center;
            background: #0f172a;
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
            color: white;
        }
        .uploaded {
            background-color: #1e293b;
            padding: 1rem;
            border-radius: 0.5rem;
            color: #ffffff;
        }
        .data-box {
            background-color: #f1f5f9;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Hero Section ---
st.markdown("""
    <div class="hero">
        <h1>📄 Insurance Policy Extractor</h1>
        <p>Upload your PDF(s) and get structured, AI-generated policy details.</p>
    </div>
""", unsafe_allow_html=True)

# --- File Uploader ---
upload_mode = st.radio("Select upload mode:", ["Single PDF", "Multiple PDFs"])
uploaded_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=(upload_mode == "Multiple PDFs"))

# --- Function to extract text ---
def extract_text_from_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# --- Function to call OpenAI ---
def extract_policy_fields(text):
    prompt = f"""
Extract the following fields from the insurance policy text.
Format the output as JSON with keys:
customer_name, policy_number, start_date, end_date, sum_insured, insurance_type, gross_amount, net_amount, od_amount, tp_amount

Text to extract from:
{text}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content

# --- Main Logic ---
if uploaded_files:
    results = []
    files = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]

    for file in files:
        st.markdown(f"<div class='uploaded'>📤 Processing: <b>{file.name}</b></div>", unsafe_allow_html=True)
        extracted_text = extract_text_from_pdf(file)
        try:
            result_raw = extract_policy_fields(extracted_text)
            result_dict = eval(result_raw)  # Safely parse JSON if returned correctly
            is_motor = result_dict.get("insurance_type", "").lower() == "motor"

            display_fields = {
                "Customer Name": result_dict.get("customer_name", ""),
                "Policy Number": result_dict.get("policy_number", ""),
                "Start Date": result_dict.get("start_date", ""),
                "End Date": result_dict.get("end_date", ""),
                "Sum Insured": result_dict.get("sum_insured", ""),
                "Insurance Type": result_dict.get("insurance_type", ""),
                "Gross Amount": result_dict.get("gross_amount", ""),
                "Net Amount": result_dict.get("net_amount", ""),
            }

            if is_motor:
                display_fields["OD Amount"] = result_dict.get("od_amount", "0")
                display_fields["TP Amount"] = result_dict.get("tp_amount", "0")

            st.markdown("<div class='data-box'>", unsafe_allow_html=True)
            for k, v in display_fields.items():
                st.markdown(f"**{k}:** {v}")
            st.markdown("</div>", unsafe_allow_html=True)

            results.append(display_fields)
        except Exception as e:
            st.error(f"❌ Error processing {file.name}: {e}")

    # --- Download CSV ---
    if results:
        df = pd.DataFrame(results)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="extracted_policy_data.csv",
            mime="text/csv"
        )

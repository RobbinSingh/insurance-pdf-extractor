# app.py
import streamlit as st
import fitz  # PyMuPDF
import tempfile
import os
import csv
import io
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- UI STYLING ---------- #
st.set_page_config(page_title="Insurance PDF Extractor", layout="centered")
st.markdown("""
    <style>
        .hero {
            background-color: #1e1e1e;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            color: #39FF14;
            box-shadow: 0 0 20px #39FF14;
        }
        .card {
            background-color: #2e2e2e;
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>📄 Insurance Policy Extractor</h1>
    <p>Upload your PDF(s) and get structured AI-generated policy details instantly.</p>
</div>
""", unsafe_allow_html=True)

# ---------- FUNCTION: PDF TEXT EXTRACTION ---------- #
def extract_text_from_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ---------- FUNCTION: EXTRACT FIELDS VIA OPENAI ---------- #
def extract_policy_fields(text):
    prompt = f"""
You are a data extraction assistant. Extract the following fields from the insurance policy text below.

Fields:
- policy_number
- start_date
- end_date
- sp_code
- customer_name
- gross_amount
- net_amount
- sum_insured
- od_amount
- tp_amount
- policy_type (Motor or Non-Motor)

IMPORTANT:
- Return only a valid raw JSON object. Do NOT add triple backticks, explanations, or text around it.
- Use `null` for fields like od_amount and tp_amount if it's not a motor policy.

Policy Text:
{text}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_response = response.choices[0].message.content.strip()

    # Fix: Strip code blocks and parse clean JSON
    try:
        if raw_response.startswith("```json"):
            raw_response = raw_response.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_response)
    except Exception as e:
        st.error("❌ Failed to parse AI response. Raw response shown below for debugging:")
        st.code(raw_response)
        raise e


# ---------- MAIN LOGIC ---------- #
mode = st.radio("Select Upload Mode", ["Single PDF", "Multiple PDFs"])

results = []

if mode == "Single PDF":
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file:
        st.success("Processing...")
        try:
            text = extract_text_from_pdf(uploaded_file)
            data = extract_policy_fields(text)
            results.append(data)
        except Exception as e:
            st.error(f"Error: {e}")

elif mode == "Multiple PDFs":
    uploaded_files = st.file_uploader("Upload Multiple PDFs", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            st.info(f"Processing {file.name}...")
            try:
                text = extract_text_from_pdf(file)
                data = extract_policy_fields(text)
                results.append(data)
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")

# ---------- DISPLAY RESULTS ---------- #
if results:
    for i, res in enumerate(results):
        st.markdown("""<div class="card">""", unsafe_allow_html=True)
        st.subheader(f"📄 Policy {i+1}")
        st.text(f"Customer Name: {res.get('customer_name')}")
        st.text(f"Policy Number: {res.get('policy_number')}")
        st.text(f"Start Date: {res.get('start_date')}  |  End Date: {res.get('end_date')}")
        st.text(f"SP Code: {res.get('sp_code')}")
        st.text(f"Gross Amount: {res.get('gross_amount')}  |  Net Amount: {res.get('net_amount')}")
        st.text(f"Sum Insured: {res.get('sum_insured')}")

        if res.get("policy_type", "").lower() == "motor":
            st.text(f"Own Damage (OD): {res.get('od_amount')}  |  Third Party (TP): {res.get('tp_amount')}")
        st.markdown("""</div>""", unsafe_allow_html=True)

    # ---------- DOWNLOAD CSV ---------- #
    csv_buffer = io.StringIO()
    fieldnames = ["customer_name", "policy_number", "start_date", "end_date", "sp_code", "gross_amount", "net_amount", "sum_insured", "od_amount", "tp_amount", "policy_type"]
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

    st.download_button("📥 Download CSV", data=csv_buffer.getvalue(), file_name="extracted_policies.csv", mime="text/csv")

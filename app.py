import streamlit as st
import fitz  # PyMuPDF
import os
import openai
import json
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Set OpenAI client
client = openai.OpenAI(api_key=api_key)

def extract_policy_data(text):
    prompt = f"""
    Extract the following information from the given insurance policy document:

    1. Name of Policy Holder
    2. Policy Number
    3. Policy Start Date
    4. Policy End Date
    5. Sum Insured
    6. Type of Insurance (Health, Life, Motor, Travel, etc.)
    7. OD Amount (only for Motor policies)
    8. TP Amount (only for Motor policies)

    If any field is not available, return "Not Found".

    Format the output as JSON with keys:
    customer name, policy_number, start_date, end_date, sum_insured, insurance_type, od_amount, tp_amount

    Document:
    """ + text

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert at reading insurance documents."},
            {"role": "user", "content": prompt},
        ],
    )

    try:
        data = json.loads(response.choices[0].message.content)
        if data.get("insurance_type", "").lower() != "motor":
            data["od_amount"] = None
            data["tp_amount"] = None
        return data
    except:
        return {"error": "Could not parse response."}

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

st.set_page_config(page_title="📄 Insurance Policy Extractor", layout="wide")
st.title("🧾 Insurance Policy PDF Extractor")
st.markdown("Upload one or more policy documents to extract details like policy number, insured amount, and more.")

mode = st.radio("Choose upload mode:", ["Single Upload", "Bulk Upload"], horizontal=True)

if mode == "Single Upload":
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file:
        with st.spinner("Processing file..."):
            text = extract_text_from_pdf(uploaded_file)
            result = extract_policy_data(text)
            st.subheader("📋 Extracted Data")

            if "error" in result:
                st.error(result["error"])
            else:
                for label, value in result.items():
                    if value and label in ["od_amount", "tp_amount"] and result.get("insurance_type", "").lower() != "motor":
                        continue
                    if value is not None and label not in ["od_amount", "tp_amount"]:
                        st.write(f"**{label.replace('_', ' ').title()}**: {value}")
                    elif label in ["od_amount", "tp_amount"] and value:
                        st.write(f"**{label.replace('_', ' ').title()}**: {value}")

                df = pd.DataFrame([result])
                csv = df.to_csv(index=False).encode('utf-8')
                json_data = json.dumps(result, indent=2).encode('utf-8')
                st.download_button("📥 Download as CSV", csv, "extracted_data.csv", "text/csv")
                st.download_button("📥 Download as JSON", json_data, "extracted_data.json", "application/json")

elif mode == "Bulk Upload":
    uploaded_files = st.file_uploader("Upload PDF Files", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        all_data = []
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                text = extract_text_from_pdf(uploaded_file)
                result = extract_policy_data(text)
                result["filename"] = uploaded_file.name
                all_data.append(result)
                st.subheader(f"📑 Extracted from {uploaded_file.name}")
                if "error" in result:
                    st.error(result["error"])
                else:
                    for label, value in result.items():
                        if value and label in ["od_amount", "tp_amount"] and result.get("insurance_type", "").lower() != "motor":
                            continue
                        if value is not None and label not in ["od_amount", "tp_amount"]:
                            st.write(f"**{label.replace('_', ' ').title()}**: {value}")
                        elif label in ["od_amount", "tp_amount"] and value:
                            st.write(f"**{label.replace('_', ' ').title()}**: {value}")

        st.subheader("📥 Download All Extracted Data")
        df = pd.DataFrame(all_data)
        csv = df.to_csv(index=False).encode('utf-8')
        json_data = json.dumps(all_data, indent=2).encode('utf-8')
        st.download_button("📦 Download as CSV", csv, "all_extracted_data.csv", "text/csv")
        st.download_button("📦 Download as JSON", json_data, "all_extracted_data.json", "application/json")

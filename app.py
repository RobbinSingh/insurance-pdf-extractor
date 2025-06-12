import os
import fitz  # PyMuPDF
import csv
import io
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

st.title("📄 Upload Insurance Policy PDF")

uploaded_file = st.file_uploader("Upload PDF file", type="pdf")

def extract_text_from_pdf(file):
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)

def extract_policy_data(text):
    prompt = f"""
You are a smart data extractor. From the following insurance policy PDF text, extract:

- Policy Holder Name
- Policy Number
- Insurance Company
- Policy Start Date
- Policy End Date
- Type of Insurance (Motor/Health/Life/etc.)
- Sum Insured
- OD Amount (Own Damage)
- TP Amount (Third Party)

Rules:
- If it's NOT a motor insurance policy, OD and TP should be '0'.
- Always return result in this exact JSON format:

{{
  "Policy Holder Name": "",
  "Policy Number": "",
  "Insurance Company": "",
  "Policy Start Date": "",
  "Policy End Date": "",
  "Type of Insurance": "",
  "Sum Insured": "",
  "OD Amount": "",
  "TP Amount": ""
}}

Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        return data
    except Exception as e:
        st.error(f"Error extracting data: {e}")
        return None

if uploaded_file:
    st.success("✅ File uploaded successfully. Extracting text...")

    text = extract_text_from_pdf(uploaded_file)
    st.info("🤖 Asking AI to extract policy data...")

    result = extract_policy_data(text)

    if result:
        st.success("🎯 Policy Data Extracted Successfully!")
        st.json(result)

        # CSV download
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=result.keys())
        writer.writeheader()
        writer.writerow(result)

        st.download_button(
            label="⬇️ Download CSV",
            data=output.getvalue(),
            file_name="extracted_policy_data.csv",
            mime="text/csv"
        )
    else:
        st.error("❌ Failed to extract policy data.")

# Save this file as standardizer_app.py
import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import BytesIO


# Accessing API key from Streamlit secrets
api_key = st.secrets["api_keys"]["my_api_key"]



# Setup Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro')


# Function to batch standardize names
def standardize_batch(list_of_names, type_):
    instruction = f"You are an expert in brand/category standardization.\n\n"
    instruction += f"For each {type_} name given, return the best standardized {type_} name.\n"
    instruction += "Format: numbered list (only the standardized names, no extra text).\n\n"

    for idx, name in enumerate(list_of_names, 1):
        instruction += f"{idx}. {name}\n"

    try:
        response = model.generate_content(instruction)
        standardized = response.text.strip().split("\n")
        standardized = [line.split('. ', 1)[1] for line in standardized]
    except Exception as e:
        standardized = ["Error"] * len(list_of_names)

    return standardized


# Streamlit UI
st.title("🛠️ Brand/Category Standardizer using Gemini AI")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your Excel file (with 'ExistingName' and blank 'DesireName' columns)",
                                 type=["xlsx"])

if uploaded_file is not None:
    # Load Excel
    df = pd.read_excel(uploaded_file)

    # Check necessary columns
    if 'ExistingName' not in df.columns or 'DesireName' not in df.columns:
        st.error("The Excel file must have 'ExistingName' and 'DesireName' columns.")
    else:
        st.success("File Uploaded Successfully!")

        st.write("Sample of your uploaded data:")
        st.dataframe(df.head())

        # Select whether Brand or Category
        type_choice = st.radio("What are you standardizing?", ["Brand", "Category"])

        if st.button("Standardize Now"):
            with st.spinner('Standardizing using AI...'):

                existing_names = df['ExistingName'].dropna().tolist()

                # Batch processing
                batch_size = 10
                batches = [existing_names[i:i + batch_size] for i in range(0, len(existing_names), batch_size)]
                standardized_names = []

                for batch in batches:
                    standardized_batch = standardize_batch(batch, type_choice.lower())
                    standardized_names.extend(standardized_batch)

                # Map back to dataframe
                df.loc[df['ExistingName'].notna(), 'DesireName'] = standardized_names

                st.success('Standardization Complete!')

                st.write("Sample of standardized data:")
                st.dataframe(df.head())

                # Prepare for download
                output = BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Download Standardized File",
                    data=output,
                    file_name="standardized_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


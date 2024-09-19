import os
import zipfile
import shutil
import re
import json
import csv
import io
import streamlit as st
import cohere

# Initialize Cohere client (replace with your API key)
cohere_client = cohere.Client('YOUR_COHERE_API_KEY')

# Streamlit Interface for uploading ZIP files
st.title("ZIP File Processor")

# Directory paths (you may adjust these based on your environment)
zip_file_location = "./uploaded_zips/"
unzip_file_location = "./unzipped_files/"
rc_file_location = "./rc_files/"

# Ensure folders exist
os.makedirs(zip_file_location, exist_ok=True)
os.makedirs(unzip_file_location, exist_ok=True)
os.makedirs(rc_file_location, exist_ok=True)

# Upload ZIP file using Streamlit's file uploader
uploaded_file = st.file_uploader("Upload a ZIP file", type="zip")

def save_uploaded_file(uploaded_file):
    file_path = os.path.join(zip_file_location, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        st.write(f"Extracted: {zip_path} to {extract_to}")

        # Recursively extract nested ZIP files
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if file.endswith('.zip'):
                    file_path = os.path.join(root, file)
                    st.write(f"Found sub-ZIP file: {file_path}")
                    sub_extract_to = os.path.join(extract_to, os.path.splitext(file)[0])
                    extract_zip(file_path, sub_extract_to)
    except zipfile.BadZipFile:
        st.error(f"Error: '{zip_path}' is not a valid ZIP file or it is corrupted.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def delete_zip_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".zip"):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                st.write(f"Deleted: {file_path}")

def copy_r_files(source_dir, target_dir, keywords):
    os.makedirs(target_dir, exist_ok=True)

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if any(keyword.lower() in file.lower() for keyword in keywords):
                file_path = os.path.join(root, file)
                destination_file_path = os.path.join(target_dir, file)

                if os.path.exists(destination_file_path):
                    file_name, file_extension = os.path.splitext(file)
                    new_file_name = f"{file_name}_2{file_extension}"
                    destination_file_path = os.path.join(target_dir, new_file_name)

                shutil.copy(file_path, destination_file_path)
                st.write(f"Copied {file_path} to {destination_file_path}")

def copy_rc_files(source_dir, target_dir):
    os.makedirs(target_dir, exist_ok=True)

    pattern = r'(^|[_\.\s])rc([_\.\s]|$)'
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if re.search(pattern, os.path.splitext(file)[0], re.IGNORECASE):
                file_path = os.path.join(root, file)
                destination_file_path = os.path.join(target_dir, file)

                if os.path.exists(destination_file_path):
                    file_name, file_extension = os.path.splitext(file)
                    new_file_name = f"{file_name}_2{file_extension}"
                    destination_file_path = os.path.join(target_dir, new_file_name)

                shutil.copy(file_path, destination_file_path)
                st.write(f"Copied {file_path} to {destination_file_path}")

def create_zip_from_folder(folder_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)
    buffer.seek(0)
    return buffer

def extract_project_details_cr_pdf(text):
    response = cohere_client.generate(
        model='command-r-plus-08-2024',
        prompt=f"Extract following detailed information from the text:\n"
               f"Synthèse des éléments pertinents :\n"
               f"2.Actions à prendre par SEF (Stores et Fermetures) :\n"
               f"Text:\n{text}"
    )

    extracted_data = response.generations[0].text.strip()

    project_info = {}
    try:
        for line in extracted_data.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                project_info[key.strip()] = value.strip()
    except Exception as e:
        return f"An error occurred during parsing: {e}"

    return project_info

def save_json_to_file(data, pdf_path):
    base_name = os.path.basename(pdf_path)
    json_name = f"{os.path.splitext(base_name)[0]}_pdf_cr_synthes.json"
    json_path = os.path.join(os.path.dirname(pdf_path), json_name)

    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return json_path

def generate_numbered_todo_list_pdf(text):
    response = cohere_client.generate(
        model='command-r-plus-08-2024',
        prompt=f'From the following text, generate a numbered list of To-Do items:\n\nText:\n{text}\n\nTo-Do List:\n1. ',
        temperature=0.7,
        max_tokens=1500
    )

    todo_list = response.generations[0].text.strip()

    formatted_todo_list = [
        f"{i+1}. {item.strip()}"
        for i, item in enumerate(todo_list.split('\n'))
        if item.strip()
    ]
    return formatted_todo_list

def save_numbered_todo_list_to_csv(todo_list, pdf_path):
    base_name = os.path.basename(pdf_path)
    csv_name = f"{os.path.splitext(base_name)[0]}_pdf_todo_list.csv"
    csv_path = os.path.join(os.path.dirname(pdf_path), csv_name)

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["To-Do List"])
            for item in todo_list:
                writer.writerow([item])
    except Exception as e:
        return f"An error occurred while saving CSV file: {e}"

    return csv_path

def process_all_pdfs_in_folder(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, file_name)
            pdf_text = extract_text_from_pdf(pdf_path)  # Ensure you have this function defined

            cr_details = extract_project_details_cr_pdf(pdf_text)
            cr_json_path = save_json_to_file(cr_details, pdf_path)
            st.write(f"CR details saved to {cr_json_path}")

            todo_list = generate_numbered_todo_list_pdf(pdf_text)
            csv_path = save_numbered_todo_list_to_csv(todo_list, pdf_path)
            st.write(f"To-Do list saved to {csv_path}")

# Main application logic
if uploaded_file is not None:
    # Save uploaded ZIP file
    zip_file_path = save_uploaded_file(uploaded_file)

    # Extract uploaded ZIP file
    extract_zip(zip_file_path, unzip_file_location)

    # Delete ZIP files after extraction
    delete_zip_files(unzip_file_location)

    # Copy specific files based on keywords (Règlement de la consultation)
    keywords = ["Règlement de la consultation", "Reglement de consultation"]
    copy_r_files(unzip_file_location, rc_file_location, keywords)

    # Copy files matching 'rc' pattern
    copy_rc_files(unzip_file_location, rc_file_location)

    # Process PDF files in the 'rc_files' directory
    process_all_pdfs_in_folder(rc_file_location)

    st.success("File processing completed!")

    # Create ZIP files for download
    unzip_zip_buffer = create_zip_from_folder(unzip_file_location)
    rc_zip_buffer = create_zip_from_folder(rc_file_location)

    st.download_button(
        label="Download Unzipped Files",
        data=unzip_zip_buffer,
        file_name="unzipped_files.zip",
        mime="application/zip"
    )

    st.download_button(
        label="Download RC Files",
        data=rc_zip_buffer,
        file_name="rc_files.zip",
        mime="application/zip"
    )
else:
    st.info("Please upload a ZIP file to begin processing.")

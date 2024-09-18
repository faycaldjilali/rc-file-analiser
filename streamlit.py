import os
import zipfile
import shutil
import re
import streamlit as st

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

def extract_all_zips_in_directory(directory, extract_root):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.zip'):
                zip_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, directory)
                extract_to_folder = os.path.join(extract_root, relative_path, os.path.splitext(file)[0])
                os.makedirs(extract_to_folder, exist_ok=True)
                st.write(f"Processing ZIP file: {zip_file_path}")
                extract_zip(zip_file_path, extract_to_folder)

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

# Main application logic
if uploaded_file is not None:
    # Save uploaded ZIP file
    zip_file_path = save_uploaded_file(uploaded_file)

    # Extract uploaded ZIP file
    extract_all_zips_in_directory(zip_file_location, unzip_file_location)

    # Delete ZIP files after extraction
    delete_zip_files(unzip_file_location)

    # Copy specific files based on keywords (Règlement de la consultation)
    keywords = ["Règlement de la consultation", "Reglement de consultation"]
    copy_r_files(unzip_file_location, rc_file_location, keywords)

    # Copy files matching 'rc' pattern
    copy_rc_files(unzip_file_location, rc_file_location)

    st.success("File processing completed!")
else:
    st.info("Please upload a ZIP file to begin processing.")

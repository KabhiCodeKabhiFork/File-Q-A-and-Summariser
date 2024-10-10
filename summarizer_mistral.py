
import streamlit as st
from tika import parser
import zipfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from mistralai import Mistral

api_key = "Enter your api key here"
model = "mistral-large-latest"

def read_file(file):
    parsed = parser.from_buffer(file)
    return parsed['content']

def read_zip(file,files):
    with zipfile.ZipFile(file) as z:
        for filename in z.namelist():
            with z.open(filename) as f:
                if filename.endswith(".pdf"):
                    files[filename] = read_file(f)
                elif filename.endswith(".docx"):
                    files[filename] = read_file(f)
                elif filename.endswith(".txt"):
                    files[filename] = read_file(f)
                elif filename.endswith(".zip"):
                    files = read_zip(f,files)
    return files

with st.sidebar:
    uploaded_file = st.file_uploader("Upload an article", type=("txt", "pdf","docx","zip"),accept_multiple_files=True)

st.title("📝 File Q&A and Summarization")


question = st.text_input(
      "Ask something about the article",
      placeholder="Can you give me a short summary?",
      disabled=not uploaded_file)

if uploaded_file and question and not api_key:
    st.info("Please add your API key to continue.")

if uploaded_file and question and api_key:
    files = {}
    for file in uploaded_file:
        if file.type=='application/pdf':
            files[file.name] = read_file(file)
        elif file.type=="application/zip":
            files = read_zip(file,files)
        elif file.type=="text/plain":
            files[file.name] = read_file(file)
        elif file.type=="application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            files[file.name] = read_file(file)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=64,
        length_function=len,
    )
    for file in files:
        files[file] = text_splitter.split_text(files[file])

    client = Mistral(api_key=api_key)
    
    files_after_summary = {}
    for file in files:
        temp = []
        for chunk in files[file]:
            response = client.chat.complete(
                model=model,
                messages=[
                    {"role": "system", "content": 'You are a helpful assistant skilled in providing accurate summaries and do it like a professional.'},
                    {"role": "user", "content": f'Question: {question} \n Text: {chunk}'},
                ],
            )
            temp.append(response.choices[0].message.content)
        files_after_summary[file] = temp

    st.write("### Answer")
    st.write(files_after_summary)

    
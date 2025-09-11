# build_rag_dataset.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def build_chroma_from_pdf(pdf_path, persist_dir="chroma_db"):
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Number Page of PDF: {len(documents)}")

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(documents)
    print(f"Chunks after splitting: {len(docs)}")

    # Embedding model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Save into ChromaDB
    vectordb = Chroma.from_documents(docs, embeddings, persist_directory=persist_dir)
    vectordb.persist()
    print(f"Saved dataset in: {persist_dir}")

    return vectordb

if __name__ == "__main__":
    data_folder = "D:\\Tuyên\\outsource\\window_trouble\\data"
    db_dir = "chroma_db"

    pdf_files = [os.path.join(data_folder, f) for f in os.listdir(data_folder) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files[:5]:  # Embed up to 5 files
        print(f"\nProcessing: {pdf_file}")
        build_chroma_from_pdf(pdf_file, db_dir)

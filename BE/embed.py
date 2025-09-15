# build_rag_dataset.py

import os
from langchain_community.document_loaders.googledrive import UnstructuredPDFLoader, Docx2txtLoader, TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from Database import log_ingestion, should_ingest
import torch


def get_vectorstore():
    persist_dir = "../chroma_db/"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": device} )
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedding_model)
    return vectordb




def Load_Document(document_type, file_name):
    if document_type == "pdf":
        loader = UnstructuredPDFLoader(file_name)
    elif document_type in [ "docx", "doc"]:
        loader = Docx2txtLoader(file_name)
    elif document_type in ["txt", "text"]:
        loader = TextLoader(file_name)
    elif document_type in ["md", "markdown"]:
        loader = UnstructuredMarkdownLoader(file_name)
    else:
        raise ValueError(f"Unsupported document type: {document_type}")
    
    documents = loader.load()
    return documents


def build_chroma_from_pdf(pdf_path, persist_dir="chroma_db"):
    # Load PDF
    loader = UnstructuredPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Number Page of PDF: {len(documents)}")

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
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
    data_folder = "C:\\Users\\ADMIN\\Desktop\\Data\\test_chunking"
    db_dir = "chroma_db"

    pdf_files = [os.path.join(data_folder, f) for f in os.listdir(data_folder) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files[:5]:  # Embed up to 5 files
        print(f"\nProcessing: {pdf_file}")
        build_chroma_from_pdf(pdf_file, db_dir)

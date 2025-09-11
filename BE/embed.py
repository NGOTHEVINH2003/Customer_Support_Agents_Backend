# build_rag_dataset.py

import os
from langchain_community.document_loaders import PyPDFLoader
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

def process_and_store(docs, source, doc_id, last_modified, metada=None):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(docs)

    # put doc_id into metadata for versioning control
    for chunks in docs:
        if chunks.metadata is None:
            chunks.metadata = {}
        chunks.metadata.update({"source": source, "document_id": doc_id, "last_modified": last_modified})
        if metada:
            chunks.metadata.update(metada)
        
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs, ids=[f"{doc_id}_{i}" for i in range (len(docs))])
    vectorstore.persist()

    log_ingestion(source, doc_id, "success", str(metada), last_modified)

def update_document(docs, source, doc_id, last_modified, metada=None):
    vectorstore = get_vectorstore()

    if should_ingest(source, doc_id, last_modified):
        #when re-ingest, delete the old version first according to doc_id
        vectorstore.delete(ids=[doc_id])
        process_and_store(docs, source, doc_id, last_modified, metada)
        print(f"Document {doc_id} from {source} ingested/updated successfully.")
    else:
        print(f"Document {doc_id} from {source} is up-to-date. Skipping ingestion.")


def build_chroma_from_pdf(pdf_path, persist_dir="../chroma_db/"):
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Number Page of PDF: {len(documents)}")

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(documents)
    print(f"Chunks after splitting: {len(docs)}")

    # Embedding model
    device = "cuda" if torch.cuda.is_available() else "cpu"

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": device} )

    # Save into ChromaDB
    vectordb = Chroma.from_documents(docs, embeddings, persist_directory=persist_dir)
    vectordb.persist()
    print(f"Saved dataset in: {persist_dir}")

    return vectordb

if __name__ == "__main__":
    data_folder = "C:\\Users\\ADMIN\\Desktop\\Data"
    db_dir = "chroma_db"

    pdf_files = [os.path.join(data_folder, f) for f in os.listdir(data_folder) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files[:5]:  # Embed up to 5 files
        print(f"\nProcessing: {pdf_file}")
        build_chroma_from_pdf(pdf_file, db_dir)

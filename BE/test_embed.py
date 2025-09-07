import os
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


# Step 2 + 3. Split with outline + Unstructured
def process_with_unstructured(file_path: str):
    """
    Load và xử lý file bằng Unstructured + Split outline.
    """
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load()

    # Split theo outline
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n# ", "\n## ", "\n### ", "\n", " ", ""]
    )
    split_docs = text_splitter.split_documents(docs)
    return split_docs


# Step 4. Embedding dataset
def embed_dataset(docs, persist_directory="db"):
    """
    Tạo embedding và lưu vào Chroma.
    """
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectordb.persist()
    return vectordb


# Step 5. Pipeline tổng
def build_dataset(local_file: str, persist_directory="db"):
    """
    Pipeline tổng để xử lý dataset:
    1. Load file (đã được n8n ingest về)
    2. Unstructured + Split outline
    3. Embedding
    4. Lưu vào DB
    """
    # Xử lý unstructured
    docs = process_with_unstructured(local_file)

    # Embedding + Lưu dataset
    vectordb = embed_dataset(docs, persist_directory=persist_directory)
    return vectordb


if __name__ == "__main__":
    local_file = "./downloads/sample.pdf"
    build_dataset(local_file, persist_directory="db")
    print("Dataset đã được xử lý và lưu vào DB")

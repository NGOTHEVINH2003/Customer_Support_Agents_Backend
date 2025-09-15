import os
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import torch

def build_chroma_from_pdf(pdf_path):
    # Load PDF
    loader = UnstructuredPDFLoader(pdf_path)

    documents = loader.load()
    print(f"Number Page of PDF: {len(documents)}")

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    docs = splitter.split_documents(documents)
    print(f"Chunks after splitting: {len(docs)}")

    for i, chunk in enumerate(docs):
        print(f"\n--- Chunk {i+1}/{len(docs)} (length: {len(chunk.page_content)}) ---")
        print(chunk.page_content)
    
    print("\n----------------------------------- Total Chunks:", len(docs))



if __name__ == "__main__":
    data_folder = "C:\\Users\\ADMIN\\Desktop\\Data\\test_chunking\\Test_Data"

    pdf_files = [os.path.join(data_folder, f) for f in os.listdir(data_folder) if f.endswith(".pdf")]

    for pdf_file in pdf_files[:5]:  # Embed up to 5 files
        build_chroma_from_pdf(pdf_file)
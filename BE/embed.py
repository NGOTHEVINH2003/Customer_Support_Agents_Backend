import os
import torch
from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader, PdfWriter
from split import split_pdf_by_outline
import shutil

# ==== CONFIG ====
CREDENTIALS_FILE = "Credential.json"   # service account JSON
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


# ===================== GOOGLE DRIVE AUTH =====================
def init_gdrive():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    return service


def list_drive_files(service, mime_type="application/pdf"):
    """Lấy danh sách file PDF"""
    results = service.files().list(
        q=f"mimeType='{mime_type}' and trashed=false",
        pageSize=1000,
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])


def download_from_gdrive_file(service, file_id, save_path: str):
    """Download file từ Google Drive"""
    from googleapiclient.http import MediaIoBaseDownload
    import io

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(save_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download {int(status.progress() * 100)}%.")
    print(f"Downloaded to {save_path}")
    return save_path


# ===================== RAG PIPELINE =====================
def process_with_unstructured(file_path: str):
    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=350
    )
    try:
        loader = UnstructuredPDFLoader(file_path)
        docs = loader.load()

        if not docs:
            print(f"⚠️ No text extracted from {file_path}, skipping.")
            return []

        split_docs = splitter.split_documents(docs)
        all_chunks.extend(split_docs)
        print(f"{os.path.basename(file_path)} → {len(split_docs)} chunks")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    print(f"Total chunks from {file_path}: {len(all_chunks)}")
    return all_chunks


def embed_dataset(docs, persist_directory="db"):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectordb.persist()
    return vectordb


def build_dataset_from_drive_file(
    file_id, file_name, service = init_gdrive(),
    persist_directory="chroma_db", tmp_dir="tmp"
):
    # 1. Download PDF từ Google Drive
    os.makedirs(tmp_dir, exist_ok=True)
    local_path = os.path.join(tmp_dir, file_name)
    download_from_gdrive_file(service, file_id, local_path)

    # 2. Tạo folder riêng để lưu PDF đã tách
    file_base = os.path.splitext(file_name)[0]
    split_dir = os.path.join(tmp_dir, file_base)
    os.makedirs(split_dir, exist_ok=True)

    # 3. Tách PDF theo outline
    split_files = split_pdf_by_outline(local_path, split_dir)

    # 4. Embed từng file PDF đã tách
    all_docs = []
    for split_pdf in split_files:
        docs = process_with_unstructured(split_pdf)
        print(f"Chunks from {os.path.basename(split_pdf)}: {len(docs)}")
        all_docs.extend(docs)

    embed_dataset(all_docs, persist_directory=persist_directory)
    
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"🧹 Cleaned up {tmp_dir}")


   

# ===================== MAIN =====================
if __name__ == "__main__":
    db_dir = "chroma_db"
    tmp_dir = "tmp_files"

    # B1: Kết nối Google Drive
    service = init_gdrive()

    # B2: Lấy danh sách toàn bộ file PDF trong Drive
    files = list_drive_files(service, mime_type="application/pdf")
    print(f"Found {len(files)} PDF files in Google Drive.")

    # B3: Xử lý từng file
    for idx, f in enumerate(files, start=1):
        print(f"\nProcessing {idx}/{len(files)}: {f['name']} ({f['id']})")
        build_dataset_from_drive_file(
            service,
            f["id"],
            f["name"],
            persist_directory=db_dir,
            tmp_dir=tmp_dir
        )

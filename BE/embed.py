import os
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from split import split_pdf_by_outline
from dotenv import load_dotenv

load_dotenv()

# ==== CONFIG ====
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
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
    """
    Download file từ Google Drive.
    Tự động handle:
      - File nhị phân (PDF, DOCX, v.v.) -> get_media
      - Google Docs / Sheets / Slides -> export_media sang định dạng tương ứng
    """
    from googleapiclient.http import MediaIoBaseDownload
    import io

    file_info = service.files().get(fileId=file_id, fields="name, mimeType").execute()
    mime_type = file_info["mimeType"]

    google_docs_mime_map = {
        "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",    # XLSX
        "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation"  # PPTX
    }

    if mime_type in google_docs_mime_map:
        request = service.files().export_media(fileId=file_id, mimeType=google_docs_mime_map[mime_type])
    else:
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

# ===================== LOADER CHO NHIỀU ĐỊNH DẠNG =====================
def load_file(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = UnstructuredPDFLoader(file_path)
    elif ext in [".docx", ".doc"]:
        loader = UnstructuredWordDocumentLoader(file_path)
    elif ext in [".xlsx", ".xls"]:
        loader = UnstructuredExcelLoader(file_path)
    elif ext in [".pptx", ".ppt"]:
        loader = UnstructuredPowerPointLoader(file_path)
    else:
        loader = UnstructuredFileLoader(file_path)  # txt, md, csv, v.v.
    return loader.load()


# ===================== RAG PIPELINE =====================
def process_with_unstructured(file_path: str):
    try:
        docs = load_file(file_path)

        all_chunks = []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=350,
            separators=["\n## ", "\n### ", "\n\n"]
        )

        if not docs:
            print(f"⚠️ No text extracted from {file_path}, skipping.")
            return []

        split_docs = splitter.split_documents(docs)

        for doc in split_docs:
                doc.metadata["filename"] = os.path.basename(file_path)


        all_chunks.extend(split_docs)
        print(f"{os.path.basename(file_path)} → {len(split_docs)} chunks")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

    print(f"Total chunks from {file_path}: {len(all_chunks)}")
    return all_chunks


def embed_dataset(docs, persist_directory="db"):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectordb.persist()
    return vectordb


def build_dataset_from_drive_file(
    file_id, file_name, service=init_gdrive(),
    persist_directory="chroma_db", tmp_dir="tmp"
):
    """"Tải file từ Drive, tách nhỏ theo outline, embed và lưu vào ChromaDB
    - file_id: ID của file trên Google Drive
    - file_name: tên file trên drive
    """
    os.makedirs(tmp_dir, exist_ok=True)
    local_path = os.path.join(tmp_dir, file_name)
    download_from_gdrive_file(service, file_id, local_path)

    if file_name.lower().endswith(".pdf"):
        file_base = os.path.splitext(file_name)[0]
        split_dir = os.path.join(tmp_dir, file_base)
        os.makedirs(split_dir, exist_ok=True)

        split_files = split_pdf_by_outline(local_path, split_dir)
    else:
        split_files = [local_path]


    all_docs = []
    for split_file in split_files:
        docs = process_with_unstructured(split_file)
        print(f"Chunks from {os.path.basename(split_file)}: {len(docs)}")
        all_docs.extend(docs)

    embed_dataset(all_docs, persist_directory=persist_directory)
    
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"🧹 Cleaned up {tmp_dir}")


def embed_local_file(
    file_path: str,
    persist_directory="chroma_db",
    tmp_dir="tmp_local",
    split_by_outline: bool = True
):
    """
    Ingest 1 file local (pdf, docx, xlsx, pptx, txt, csv...) vào ChromaDB
    - file_path: đường dẫn file local
    - persist_directory: thư mục ChromaDB
    - tmp_dir: thư mục tạm để lưu split
    - split_by_outline: nếu True và file là PDF thì tách outline
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    os.makedirs(tmp_dir, exist_ok=True)
    file_name = os.path.basename(file_path)

    all_docs = []
    if file_path.lower().endswith(".pdf") and split_by_outline:
        file_base = os.path.splitext(file_name)[0]
        split_dir = os.path.join(tmp_dir, file_base)
        os.makedirs(split_dir, exist_ok=True)

        split_files = split_pdf_by_outline(file_path, split_dir)

        for split_pdf in split_files:
            docs = process_with_unstructured(split_pdf)
            all_docs.extend(docs)
    else:
        docs = process_with_unstructured(file_path)
        all_docs.extend(docs)

    if not all_docs:
        print(f"⚠️ No docs extracted from {file_name}, skipping embed.")
        return None

    embed_dataset(all_docs, persist_directory=persist_directory)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"✅ Embedded {file_name} into {persist_directory}")
    return True



# ===================== MAIN =====================
if __name__ == "__main__":
    db_dir = "chroma_db"
    tmp_dir = "tmp_files"
    data_folder = r"C:\Users\ADMIN\Desktop\Data\test_chunking\Test_Data"

    alldocs = []
    for f in os.listdir(data_folder):
        file_path = os.path.join(data_folder, f)
        if not os.path.isfile(file_path):
            continue
        docs = process_with_unstructured(file_path)
        alldocs.extend(docs)

    embed_dataset(alldocs, persist_directory=db_dir)

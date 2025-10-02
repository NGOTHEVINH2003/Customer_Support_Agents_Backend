# Customer Support Agents Backend

A Windows troubleshooting assistant powered by RAG (Retrieval-Augmented Generation), FastAPI, and Streamlit. This project enables ingestion of documents, semantic search, feedback analytics, and escalation monitoring.

## Features

- **RAG Chatbot**: Answers troubleshooting questions using context from ingested documents.
- **Document Ingestion**: Supports PDF, DOCX, XLSX, PPTX, TXT, CSV from local upload or Google Drive.
- **Feedback Analytics**: Tracks negative feedback trends and hard questions.
- **Escalation Alerts**: Monitors and displays escalated queries.
- **Reporting & Email**: Generates daily/weekly reports and sends via email.
- **Admin Dashboard**: Streamlit frontend for monitoring and management.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Customer_Support_Agents_Backend.git
cd Customer_Support_Agents_Backend
```

### 2. Install Dependencies

Create a virtual environment and install requirements:

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Google API, email, and database paths.

### 4. Initialize the Database

```bash
python BE/Database.py
```

### 5. Start the Backend API

```bash
uvicorn BE.app:app --reload
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 6. Launch the Frontend Dashboard

```bash
streamlit run FE/Overview.py
```

Access the dashboard at [http://localhost:8501](http://localhost:8501).

## Usage

- **Ingest Documents**: Use the dashboard to upload files or trigger Google Drive ingestion.
- **Ask Questions**: Send queries via API or dashboard; answers are generated using RAG and Gemini.
- **Feedback & Escalation**: React to answers with thumbs up/down; escalated queries are tracked.
- **Analytics & Reports**: View feedback trends, hard questions, and send reports via email.

## API Endpoints

- `POST /query`: Ask a question.
- `POST /ingest_local`: Ingest local files.
- `POST /ingest_drive`: Ingest files from Google Drive.
- `GET /get-metrics`: Get dashboard metrics.
- `GET /get-negative-feedback-trend`: Feedback analytics.
- `GET /get-ingestion-history`: Ingestion logs.
- `GET /show-hard-questions`: Hard question analytics.
- `POST /send-email`: Send daily/weekly report.

See [http://localhost:8000/docs](http://localhost:8000/docs) for full API documentation.

## Folder Structure

```
BE/         # Backend (FastAPI, RAG, DB, ingestion)
FE/         # Frontend (Streamlit dashboard)
.env        # Environment variables
requirements.txt
```

## Troubleshooting

- Ensure all environment variables are set.
- Check database initialization if you see missing tables.
- For Google Drive ingestion, verify credentials and API access.
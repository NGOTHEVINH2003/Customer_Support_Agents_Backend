import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from bot import ask_question
from embed import build_chroma_from_pdf
from fastapi import UploadFile, File
from Models import Query, IngestionLog, Feedback
from Database import log_query, updated_flagged_status

app = FastAPI(title = "Windows Troubleshooting QA API")
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/query-test")
async def ask_test(query: str):
    try:
        answer = await ask_question(query)
        return {"question": query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ingest-data-test")
async def ingest_data_test(file: UploadFile= File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        build_chroma_from_pdf(file_location)
        os.remove(file_location)
        return {"status": "success", "message": f"Data from {file.filename} ingested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_endpoint(query: Query): 
    try:
        answer = await ask_question(query.question)
        log_id = log_query(query.question_id,query.question, answer, query.similarity_score)
        return {"log_id": log_id, "question": query.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ingest")
async def ingest_endpoint(ingestion_log: IngestionLog):
    try:
        build_chroma_from_pdf(ingestion_log.document_id)
        return {"status": "success", "message": f"Data from {ingestion_log.document_id} ingested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/feedback")
async def feedback(feedback: Feedback):
    try:
        updated_flagged_status(feedback.question_id, feedback.flagged)
        return {"status": "success", "message": "Feedback recorded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from bot import ask_question
from embed import build_chroma_from_pdf
from fastapi import UploadFile, File

app = FastAPI(title = "Windows Troubleshooting QA API")
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
@app.post("/query")
async def ask(query: str):
    try:
        answer = await ask_question(query)
        return {"question": query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ingest-data")
async def ingest_data(file: UploadFile= File(...)):
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


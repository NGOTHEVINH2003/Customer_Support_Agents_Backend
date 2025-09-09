from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import asyncio
from bot import ask_question

app = FastAPI(title = "Windows Troubleshooting QA API")
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
@app.post("/ask")
async def ask(query: str):
    try:
        answer = await ask_question(query)
        return {"question": query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

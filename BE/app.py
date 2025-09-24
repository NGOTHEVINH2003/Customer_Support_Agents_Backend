import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from bot import ask_question
from embed import build_dataset_from_drive_file
from fastapi import UploadFile, File
from Models import Query, IngestionLog, Feedback, Reaction, IngestionList
from Database import log_query, updated_flagged_status, update_reaction_added, update_reaction_removed, should_ingest, upsert_log
from smtp import SendEmail
from metrics import GetMetrics, GetNegativeFeedbackTrend, GetIngestionHistory, ShowHardQuestions
from report import QueryDailyData, QueryWeeklyData, CreateReport, GetToday, GetWeekRange


app = FastAPI(title = "Windows Troubleshooting QA API")
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/query-test")
def ask_test(query: str):
    try:
        answer = ask_question(query)
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
        build_dataset_from_drive_file(file_location)    
        os.remove(file_location)
        return {"status": "success", "message": f"Data from {file.filename} ingested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_endpoint(query: Query): 
    try:
        answer = ask_question(query.question)
        log_id = log_query(query.question_id,query.user_id, query.channel_id,query.question, answer["answer"], answer["similarity_confidence"])
        return {"log_id": log_id, "question": query.question, "answer": answer["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ingest")
async def ingest_endpoint(payload: IngestionList):
    try:
        # build_chroma_from_pdf(ingestion_log.document_id)
        for document in payload.documents:
            if (should_ingest(document.source,document.document_id, document.last_modified) and document.document_type == "application/pdf"):
                print(f"Starting ingestion for {document.document_name}...")
                build_dataset_from_drive_file(document.document_id, document.document_name)
                upsert_log(document.source, document.document_id, document.document_type, document.document_name, "success", document.last_modified)
            else: print(f"Skipping ingestion for {document.document_name} as it is up-to-date.")
        return {"status": "success", "message": "Ingestion process completed."}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    
@app.post("/feedback")
async def feedback(feedback: Feedback):
    try:
        ##updated_flagged_status(feedback.question_id, feedback.flagged)
        return {"status": "success", "message": "Feedback recorded successfully.", "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/reaction_received")
async def reaction_added(reaction: Reaction):
    try:

        if reaction.reaction_type not in ["reaction_added", "reaction_removed"]:
            raise HTTPException(status_code=400, detail="Invalid reaction type.")
        if reaction.reaction_name not in ["1", "-1"]:
            raise HTTPException(status_code=400, detail="Invalid reaction name.")
        
        if reaction.reaction_type == "reaction_added":
            if reaction.reaction_name == "-1" :
                update_reaction_added(reaction.question_id, thumbs_up=False, thumbs_down=True);
            elif reaction.reaction_name == "1":
                update_reaction_added(reaction.question_id, thumbs_up=True, thumbs_down=False);
        else: 
            if reaction.reaction_name == "-1" :
                update_reaction_removed(reaction.question_id, thumbs_up=False, thumbs_down=-1);
            elif reaction.reaction_name == "1":
                update_reaction_removed(reaction.question_id, thumbs_up=-1, thumbs_down=False);
        
        return {"status": "success", "message": "Reaction recorded successfully.", "reaction": reaction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email")
def send_email(reportType: str):
    try:
        if reportType == "daily":
            df = QueryDailyData()
            today = GetToday()
            start_week = end_week = today
        else:
            df = QueryWeeklyData()
            start_week, end_week = GetWeekRange()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for the specified period.")
        
        excelFile = CreateReport(df)
        SendEmail(reportType, excelFile, start_week, end_week if reportType == "weekly" else None)

        return {"message": f"{reportType.capitalize()} report sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-metrics")
async def get_metrics():
    try:
        today_count, week_count, month_count, ai_answered, escalated, escalated_table  = GetMetrics()
        return {
            "status": "success", 
            "metrics": {
                "today_count": today_count,
                "week_count": week_count,
                "month_count": month_count,
                "ai_answered": ai_answered,
                "escalated": escalated,
                "escalated_table": escalated_table
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/get-negative-feedback-trend")
async def get_negative_feedback_trend():
    try:
        df = GetNegativeFeedbackTrend()
        if df.empty:
            return JSONResponse(content={"status": "success", "data": []})
        data = df.to_dict(orient="records")
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/get-ingestion-history")
async def get_ingestion_history():
    try:
        df = GetIngestionHistory()
        if df.empty:
            return JSONResponse(content={"status": "success", "data": []})
        data = df.to_dict(orient="records")
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/show-hard-questions")
async def show_hard_questions():
    try:
        df = ShowHardQuestions()
        if df.empty:
            return JSONResponse(content={"status": "success", "data": []})
        data = df.to_dict(orient="records")
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
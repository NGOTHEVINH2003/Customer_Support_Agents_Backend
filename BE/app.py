import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List
from fastapi import UploadFile, File, HTTPException
from bot import ask_question
from embed import build_dataset_from_drive_file, embed_local_file
from Models import Query, IngestionList, Reaction
from Database import (
    log_query,
    update_reaction_added,
    update_reaction_removed,
    should_ingest,
    insert_ingestion_log,
)
from smtp import SendEmail
from metrics import (
    GetMetrics,
    GetNegativeFeedbackTrend,
    GetIngestionHistory,
    ShowHardQuestions,
)
from report import (
    QueryDailyData,
    QueryWeeklyData,
    CreateReport,
    GetToday,
    GetWeekRange,
)


app = FastAPI(title="Windows Troubleshooting QA API")


# ------------------------------------------------------
# Root
# ------------------------------------------------------
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


# ------------------------------------------------------
# Query endpoints
# ------------------------------------------------------
@app.post("/query-test")
def ask_test(query: str):
    try:
        answer = ask_question(query)
        log_id = log_query(
            "test_qid",
            "test_user",
            "test_channel",
            query,
            answer["answer"],
            answer["final_confidence"],
        )
        return {
            "log_id": log_id,
            "question": query,
            "answer": answer["answer"],
            "answer_confidence": answer["final_confidence"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_endpoint(query: Query):
    try:
        answer = ask_question(query.question)
        log_id = log_query(
            query.question_id,
            query.user_id,
            query.channel_id,
            query.question,
            answer["answer"],
            answer["final_confidence"],
        )
        return {
            "log_id": log_id,
            "question": query.question,
            "answer": answer["answer"],
            "similarity_confidence": answer["final_confidence"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------
# Ingestion endpoints
# ------------------------------------------------------
@app.post("/ingest_drive")
async def ingest_drive(payload: IngestionList):
    try:
        for document in payload.documents:
            if should_ingest(
                document.document_id, document.last_modified
            ):
                print(f"Starting ingestion for {document.document_name}...")
                build_dataset_from_drive_file(
                    document.document_id, document.document_name
                )
                insert_ingestion_log(
                    document.source,
                    document.document_id,
                    document.document_type,
                    document.document_name,
                    "success",
                    document.last_modified,
                )
            else:
                print(
                    f"Skipping ingestion for {document.document_name} (up-to-date)."
                )

        return {"status": "success", "message": "Ingestion process completed."}
    except Exception as e:
        return {"status": "failed", "message": str(e)}




@app.post("/ingest_local")
async def ingest_local(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        temp_path = f"temp_{file.filename}"
        try:
            with open(temp_path, "wb") as f:
                f.write(await file.read())

            embed_local_file(temp_path)

            insert_ingestion_log(
                source="local_upload",
                document_id="N/A",
                document_type=file.content_type or "unknown",
                document_name=file.filename,
                status="success",
                last_modified=None
            )

            results.append({
                "file": file.filename,
                "status": "success",
                "message": f"{file.filename} ingested successfully."
            })

        except Exception as e:
            insert_ingestion_log(
                source="local_upload",
                document_id="N/A",
                document_type=file.content_type or "unknown",
                document_name=file.filename,
                status="failed",
                last_modified=None
            )
            results.append({
                "file": file.filename,
                "status": "failed",
                "message": str(e)
            })

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return {"results": results}


# ------------------------------------------------------
# Feedback & Reactions
# ------------------------------------------------------
@app.post("/reaction_received")
async def reaction_received(reaction: Reaction):
    try:
        if reaction.reaction_type not in ["reaction_added", "reaction_removed"]:
            raise HTTPException(status_code=400, detail="Invalid reaction type.")
        if reaction.reaction_name not in ["+1", "-1"]:
            raise HTTPException(status_code=400, detail="Invalid reaction name.")

        if reaction.reaction_type == "reaction_added":
            if reaction.reaction_name == "-1":
                update_reaction_added(reaction.question_id, thumbs_up= False, thumbs_down= True)
            elif reaction.reaction_name == "+1":
                update_reaction_added(reaction.question_id, thumbs_up= True, thumbs_down= False)
        else:
            if reaction.reaction_name == "-1":
                update_reaction_removed(reaction.question_id, thumbs_up= False, thumbs_down= True)
            elif reaction.reaction_name == "+1":
                update_reaction_removed(reaction.question_id, thumbs_up= True, thumbs_down=False)

        return {
            "status": "success",
            "message": "Reaction recorded successfully.",
            "reaction": reaction,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------
# Reports & Emails
# ------------------------------------------------------
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
            raise HTTPException(status_code=404, detail="No data available.")

        excelFile = CreateReport(df)
        SendEmail(reportType, excelFile, start_week, end_week if reportType == "weekly" else None)

        return {"message": f"{reportType.capitalize()} report sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------
# Metrics & Analytics
# ------------------------------------------------------
@app.get("/get-metrics")
async def get_metrics():
    try:
        today_count, week_count, month_count, ai_answered, escalated, escalated_table = GetMetrics()
        return {
            "status": "success",
            "metrics": {
                "today_count": today_count,
                "week_count": week_count,
                "month_count": month_count,
                "ai_answered": ai_answered,
                "escalated": escalated,
                "escalated_table": escalated_table,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-negative-feedback-trend")
async def get_negative_feedback_trend():
    try:
        df = GetNegativeFeedbackTrend()
        if df.empty:
            return JSONResponse(content={"status": "success", "data": []})
        return JSONResponse(content={"status": "success", "data": df.to_dict(orient="records")})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-ingestion-history")
async def get_ingestion_history():
    try:
        df = GetIngestionHistory()
        if df.empty:
            return JSONResponse(content={"status": "success", "data": []})
        return JSONResponse(content={"status": "success", "data": df.to_dict(orient="records")})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/show-hard-questions")
async def show_hard_questions():
    try:
        df = ShowHardQuestions()
        if df.empty:
            return JSONResponse(content={"status": "success", "data": []})
        return JSONResponse(content={"status": "success", "data": df.to_dict(orient="records")})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

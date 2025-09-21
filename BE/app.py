import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from bot import ask_question
from embed import build_dataset_from_drive_file
from fastapi import UploadFile, File
from Models import Query, IngestionLog, Feedback, Reaction, IngestionList
from Database import log_query, updated_flagged_status, update_reaction_added, update_reaction_removed


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
        build_dataset_from_drive_file(payload.documents[1].document_id, payload.documents[1].document_name)

        return {"received_documents": len(payload.documents), "files": payload.documents[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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

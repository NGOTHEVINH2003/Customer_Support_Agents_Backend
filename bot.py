import os
from langchain_community.vectorstores import Chroma 
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain.prompts import PromptTemplate 
from langchain.chains import RetrievalQA 
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ["GOOGLE_API_KEY"] = "AIzaSyB1NhXVpfN3DsICHkqCFcg-LyysItTFWbk"

# Load data
persist_dir = "chroma_db" 
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedding_model) 

# Retriever
retriever = vectordb.as_retriever(search_kwargs={"k": 3}) 

# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
) 

# Custom prompt
prompt_template = PromptTemplate(
    input_variables=["context", "question"], 
    template="""You are a Windows troubleshooting assistant.
Based only on the information provided in the context, answer the user's question in English.
Your answer must strictly follow this structured format:

---
**Error Overview**  
(Briefly describe what the error is and when it happens)

**Symptoms**  
- List the common symptoms or signs when this error occurs

**Causes**  
- List the possible causes of this error (e.g., corrupted system files, registry issues, Active Directory problems, etc.)

**Solutions**  
- Provide recommended solutions or step-by-step fixes to resolve the issue
---

Instructions:
- Only use information from the context.
- If the context does not contain relevant information, clearly state:  
  "The dataset does not provide information about this error."
- Do not fabricate or assume facts.
- Always answer in English only.

Context:
{context}

Question: {question}

Answer:"""
)

qa_chain = RetrievalQA.from_chain_type( 
    llm=llm, 
    retriever=retriever, 
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template},
    return_source_documents=True  # take source documents (for confidence calculation)
)

# Query with confidence
def ask_question(query):
    try:
        result = qa_chain(query)  
        answer = result["result"]
        docs = result["source_documents"]

        # --- 1. Similarity Confidence ---
        query_emb = embedding_model.embed_query(query)
        doc_emb = embedding_model.embed_query(docs[0].page_content)
        # cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        sim_score = float(cosine_similarity([query_emb], [doc_emb])[0][0])

        # scale 
        sim_conf = round(sim_score * 100, 2)

        # --- 2. LLM Confidence ---
        conf_prompt = f"""
        Question: {query}
        Answer: {answer}

        From 0 to 100, how confident are you that the answer fully matches the context and is correct?
        Reply with only a number (0-100).
        """
        llm_conf = llm.invoke(conf_prompt).content.strip()
        try:
            llm_conf = float(llm_conf)
        except:
            llm_conf = 50.0  # fallback if LLM returns invalid number

        # --- 3. Final Confidence (average of 2 sources) ---
        final_conf = round((sim_conf + llm_conf) / 2, 2)

        return {
            "answer": answer,
            "similarity_confidence": sim_conf,
            "llm_confidence": llm_conf,
            "final_confidence": final_conf
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    query = input("Enter question: ")
    result = ask_question(query)
    print("\n--- Chatbot Output ---")
    print("Question:", query)
    print("Answer:", result.get("answer"))
    print("Similarity Confidence:", result.get("similarity_confidence"))
    print("LLM Confidence:", result.get("llm_confidence"))
    print("Final Confidence:", result.get("final_confidence"))

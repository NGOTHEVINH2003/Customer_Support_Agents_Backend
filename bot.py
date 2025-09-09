import os
from langchain_community.vectorstores import Chroma 
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain.prompts import PromptTemplate 
from langchain.chains import RetrievalQA 
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ["GOOGLE_API_KEY"] = "AIzaSyB1NhXVpfN3DsICHkqCFcg-LyysItTFWbk"

# Load datadata
persist_dir = "chroma_db" 
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedding_model) 

# RRetriever
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
Your answer must be strictly based on the dataset and should not fabricate any information.

For each question, provide the following if available:
1. The error the user encountered.
2. The possible causes of the error.
3. The recommended solutions or steps to resolve the issue.

Instructions:
- Only use information from the context.
- If the context does not contain relevant information, clearly state that.
- Do not invent or assume any facts.
- Answer in English only.

Context:
{context}

Question: {question}

Answer:"""
)

# chain RAG
qa_chain = RetrievalQA.from_chain_type( 
    llm=llm, 
    retriever=retriever, 
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
) 

# Query
async def ask_question(query):
    try:
        answer = qa_chain.run(query)
        return answer
    except Exception as e:
        return f"Lỗi: {str(e)}"

# Test
if __name__ == "__main__":
    query = input("Enter question: ")
    answer = ask_question(query)
    
    print("Câu hỏi:", query) 
    print("Trả lời:", answer)
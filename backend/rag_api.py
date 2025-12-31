# from fastapi import FastAPI, File, UploadFile, Form
# from fastapi.middleware.cors import CORSMiddleware
# import os
# import tempfile
# from dotenv import load_dotenv
# from flashrank import Ranker
# from groq import Groq
# from llama_parse import LlamaParse
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import FastEmbedEmbeddings
# from langchain_community.vectorstores import FAISS
# from langchain_classic.retrievers import ContextualCompressionRetriever
# from langchain_classic.retrievers.document_compressors import FlashrankRerank
# from langchain_core.documents import Document

# load_dotenv()

# app = FastAPI()

# # Enable CORS for Streamlit frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# def generate_summary_with_groq(user_query, retrieved_chunks, output_format):
#     """Generate response based on output format"""
#     context_text = "\n\n".join([doc.page_content for doc in retrieved_chunks])
    
#     # Adjust prompt based on format
#     format_instructions = {
#         "Executive Bullets": "Provide a concise bullet-point summary with key findings.",
#         "Technical Narrative": "Provide a detailed technical narrative with comprehensive analysis.",
#         "Compliance Matrix": "Create a structured compliance checklist with requirements and statuses."
#     }
    
#     system_prompt = f"""
#     You are a Senior Technical Tender Analyst. Your job is to extract precise information 
#     from the provided tender documents to answer the user's question.
    
#     Output Format: {format_instructions.get(output_format, format_instructions["Executive Bullets"])}
    
#     Rules:
#     - Answer ONLY based on the provided Context.
#     - If the answer is not in the context, say "Data not found in the provided documents."
#     - Be detailed and professional.
#     - Cite specific section names if available.
#     """
    
#     user_prompt = f"""
#     Context Data:
#     {context_text}
    
#     User Question: 
#     {user_query}
    
#     Provide a detailed, structured response:
#     """

#     chat_completion = groq_client.chat.completions.create(
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt}
#         ],
#         model="llama-3.3-70b-versatile",
#         temperature=0.3,
#     )
    
#     return chat_completion.choices[0].message.content

# def process_rag_pipeline(pdf_path, query, output_format, depth):
#     """Main RAG pipeline"""
#     print(f"\n1️⃣ Parsing PDF...")
#     parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY"), result_type="markdown")
#     llama_docs = parser.load_data(pdf_path)
    
#     langchain_docs = [
#         Document(page_content=d.text, metadata=d.metadata or {}) 
#         for d in llama_docs
#     ]
    
#     print(f"\n2️⃣ Chunking text...")
#     chunk_size = 2000 if depth == "Deep Dive" else 1000
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=200)
#     docs = text_splitter.split_documents(langchain_docs)
    
#     print(f"\n3️⃣ Creating vector store...")
#     embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
#     vectorstore = FAISS.from_documents(docs, embeddings)
    
#     k_value = 30 if depth == "Deep Dive" else 20
#     base_retriever = vectorstore.as_retriever(search_kwargs={"k": k_value})
    
#     print(f"\n4️⃣ Reranking...")
#     compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
#     compression_retriever = ContextualCompressionRetriever(
#         base_compressor=compressor, 
#         base_retriever=base_retriever
#     )
    
#     print(f"\n🔎 Searching for: '{query}'")
#     compressed_docs = compression_retriever.invoke(query)[:5]
    
#     print(f"\n🧠 Generating answer...")
#     final_answer = generate_summary_with_groq(query, compressed_docs, output_format)
    
#     return final_answer

# @app.post("/analyze-tender")
# async def analyze_tender(
#     file: UploadFile = File(...),
#     query: str = Form("Provide a comprehensive summary of this tender document"),
#     output_format: str = Form("Executive Bullets"),
#     depth: str = Form("Standard")
# ):
#     """
#     Endpoint to analyze uploaded tender PDF
#     """
#     try:
#         # Save uploaded file temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             content = await file.read()
#             tmp_file.write(content)
#             tmp_path = tmp_file.name
        
#         # Process with RAG pipeline
#         result = process_rag_pipeline(tmp_path, query, output_format, depth)
        
#         # Cleanup
#         os.unlink(tmp_path)
        
#         return {
#             "status": "success",
#             "summary": result,
#             "query": query,
#             "format": output_format
#         }
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }

# @app.get("/")
# def home():
#     return {"message": "TenderFlow RAG API is Running!"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)




from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import shutil
from dotenv import load_dotenv
from flashrank import Ranker
from groq import Groq
from llama_parse import LlamaParse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import FlashrankRerank
from langchain_core.documents import Document

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- CORE LOGIC FUNCTIONS ---

def generate_summary_with_groq(user_query, retrieved_chunks, output_format):
    """Generates the final summary using Groq."""
    context_text = "\n\n".join([doc.page_content for doc in retrieved_chunks])
    
    system_instruction = f"""
    You are an expert Tender Analyst. Use the provided Context to answer the user's Request.
    
    OUTPUT FORMAT: {output_format}
    
    GUIDELINES:
    - If format is 'Executive Bullets', use clear, punchy bullet points.
    - If format is 'Technical Narrative', write in professional prose.
    - If format is 'Compliance Matrix', list requirements vs compliance status.
    - STRICTLY base your answer on the provided Context.
    """

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Context:\n{context_text}\n\nRequest: {user_query}"}
    ]
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=2048
    )
    
    return response.choices[0].message.content

def process_rag_pipeline(pdf_path, query, output_format, depth):
    """
    Processes the specific PDF uploaded for this request.
    CRITICAL: Creates a FRESH Vector Store every time.
    """
    print(f"--- 1. Processing New File: {pdf_path} ---")
    
    # 1. Parse PDF
    parser = LlamaParse(result_type="markdown")
    llama_docs = parser.load_data(pdf_path)
    
    # Convert to LangChain format
    docs = [Document(page_content=d.text, metadata=d.metadata or {}) for d in llama_docs]
    
    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)
    
    # 3. Create FRESH Vector Store (Local Scope)
    # We do NOT use a global variable here to avoid 'caching' old files
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    
    # 4. Retrieve
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10}) # Fetch broad context
    
    # 5. Rerank (Optional but recommended)
    try:
        compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, 
            base_retriever=retriever
        )
        # Use the USER QUERY, not a hardcoded one
        print(f"--- Searching for: {query} ---")
        compressed_docs = compression_retriever.invoke(query)[:5]
    except Exception as e:
        print(f"Rerank failed, falling back to standard retrieval: {e}")
        compressed_docs = retriever.invoke(query)[:5]

    # 6. Generate
    return generate_summary_with_groq(query, compressed_docs, output_format)

# --- API ENDPOINTS ---

@app.post("/analyze-tender")
async def analyze_tender(
    file: UploadFile = File(...),
    query: str = Form("Provide a comprehensive summary of this tender document"),
    output_format: str = Form("Executive Bullets"),
    depth: str = Form("Standard")
):
    try:
        # Create a temp file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Run the pipeline
        result = process_rag_pipeline(tmp_path, query, output_format, depth)
        
        # Cleanup
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "summary": result
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
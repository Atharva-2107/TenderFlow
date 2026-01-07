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




from fastapi import FastAPI, File, UploadFile, Form, HTTPException
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
from langchain_community.document_loaders import PyPDFLoader
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
embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# --- CORE LOGIC FUNCTIONS ---

# Configuration
INDEX_DIR = "indices"
os.makedirs(INDEX_DIR, exist_ok=True)

# Generate Prompt Templates
SECTION_PROMPTS = {
    "Eligibility Response": """
        Extract all organizational eligibility criteria, financial requirements (turnover, net worth), 
        and technical experience requirements. For each, state the requirement and provide a draft response 
        confirming compliance. Mention specific clause numbers if available.
    """,
    "Technical Proposal": """
        Create a detailed Technical Proposal structure based on the Scope of Work. 
        Include:
        1. Understanding of Project Scope
        2. Proposed Methodology (Phase-wise)
        3. Technology Stack / Materials proposed
        4. Project Schedule and Milestones
        Focus on technical specs found in the document.
    """,
    "Financial Statements": """
        Identify all financial document requirements. List:
        1. Required Turnover details
        2. Solvency Certificate requirements
        3. Bank Guarantee formats and values
        4. Earnest Money Deposit (EMD) methodology
    """,
    "Declarations & Forms": """
        List all mandatory declarations, affidavits, and forms mentioned in the tender. 
        Provide a summary what each form certifies (e.g., Non-blacklisting, Integrity Pact).
    """
}

def get_index_path(filename: str):
    """Returns the path for the FAISS index of a specific file."""
    # Sanitize filename to be safe for directory names
    safe_name = "".join(x for x in filename if x.isalnum() or x in "._-")
    return os.path.join(INDEX_DIR, safe_name)

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

@app.post("/upload-tender")
async def upload_tender(
    file: UploadFile = File(...),
    parsing_mode: str = Form("Fast") # Options: "Fast", "High-Quality"
):
    """
    Ingests a PDF: Parses -> Chunks -> Indexes -> Saves Index to Disk.
    parsing_mode: "Fast" (PyMuPDF/PyPDF) or "High-Quality" (LlamaParse Vision)
    """
    index_path = get_index_path(file.filename)
    
    # optimization: check if index already exists
    if os.path.exists(index_path):
        return {
            "status": "success", 
            "message": "File already indexed.",
            "filename": file.filename,
            "cached": True
        }

    try:
        # 1. Save locally for parsing
        with open(f"temp_{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        docs = []
        if parsing_mode == "High-Quality":
            # 2a. Parse with LlamaParse (Cloud Vision)
            print(f"Parsing {file.filename} with LlamaParse (Vision)...")
            parser = LlamaParse(result_type="markdown")
            llama_docs = parser.load_data(f"temp_{file.filename}")
            docs = [Document(page_content=d.text, metadata=d.metadata or {}) for d in llama_docs]
        else:
            # 2b. Parse PDF with PyPDFLoader (Local, Fast)
            print(f"Parsing {file.filename} locally...")
            loader = PyPDFLoader(f"temp_{file.filename}")
            docs = loader.load()
        
        # 3. Split
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        split_docs = text_splitter.split_documents(docs)
        
        # 4. Index & Save
        print("Creating Vector Store...")
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        vectorstore.save_local(index_path)
        
        # Cleanup
        os.remove(f"temp_{file.filename}")
        
        return {
            "status": "success", 
            "message": "File indexed successfully.",
            "filename": file.filename,
            "cached": False
        }

    except Exception as e:
        print(f"ERROR in upload_tender: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-section")
async def generate_section(
    filename: str = Form(...),
    section_type: str = Form(...),
    tone: str = Form("Formal"),
    compliance_mode: bool = Form(True)
):
    """
    Generates content for a specific section using the pre-built index.
    """
    index_path = get_index_path(filename)
    
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Tender document not found. Please upload first.")
    
    try:
        # 1. Load Index
        vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
        
        # 2. Select Query based on Section
        query = SECTION_PROMPTS.get(section_type, f"Summarize information relevant to {section_type}")
        
        # 3. Retrieve Context
        docs = retriever.invoke(query)
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 4. Generate with LLM
        system_instruction = f"""
        You are a Proposal Writer for large enterprise tenders.
        Task: Write the '{section_type}' section for a bid response.
        
        Tone: {tone}
        Strict Compliance: {'Enabled' if compliance_mode else 'Disabled'}
        
        Guidelines:
        - Use professional, bid-winning language.
        - Cite specific clauses from the Context if available (e.g., [Clause 2.1]).
        - If Strict Compliance is enabled, explicitly state how we meet each requirement.
        - Do not hallucinate requirements not present in the text.
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Context:\n{context_text}\n\nDraft the response:"}
            ],
            temperature=0.3
        )
        
        return {
            "status": "success",
            "section": section_type,
            "content": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
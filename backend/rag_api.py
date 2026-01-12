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
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import nest_asyncio

# Prevent event loop errors in async contexts
nest_asyncio.apply()

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

# Generate Prompt Templates - Enhanced for Legal Grade Output
SECTION_PROMPTS = {
    "Eligibility Response": """
        Extract all organizational eligibility criteria, financial requirements (turnover, net worth), 
        and technical experience requirements from the tender document.
        
        MANDATORY OUTPUT FORMAT:
        
        ### Compliance Matrix
        Start with this table (REQUIRED):
        | Clause | Requirement | Compliance Status | Reference |
        |--------|-------------|-------------------|-----------|
        
        Then structure the response with formal legal numbering:
        
        ### 1. Organizational Eligibility
        #### 1.1 Legal Entity Requirements
        #### 1.2 Registration & Licensing
        
        ### 2. Financial Requirements
        #### 2.1 Turnover Requirements
        #### 2.2 Net Worth Requirements
        
        ### 3. Technical Experience
        #### 3.1 Past Project Experience
        #### 3.2 Key Personnel Requirements
        
        ### 4. Summary Table of Key Deliverables
        | S.No | Deliverable | Deadline | Responsible Party |
        |------|-------------|----------|-------------------|
        
        Use **bold** for all requirement headers and key amounts.
        If information is missing, use placeholder: [CLAUSE NOT FOUND - TO BE VERIFIED]
    """,
    "Technical Proposal": """
        Create a detailed Technical Proposal structure based on the Scope of Work found in the tender.
        
        MANDATORY OUTPUT FORMAT:
        
        ### Compliance Matrix
        Start with this table (REQUIRED):
        | Clause | Requirement | Compliance Status | Reference |
        |--------|-------------|-------------------|-----------|
        
        Then structure with formal legal numbering:
        
        ### 1. Understanding of Project Scope
        #### 1.1 Project Overview
        #### 1.2 Key Objectives
        #### 1.3 Scope Boundaries
        
        ### 2. Proposed Methodology
        #### 2.1 Phase-wise Approach
        #### 2.2 Quality Assurance Framework
        #### 2.3 Risk Mitigation Strategy
        
        ### 3. Technology Stack / Materials Proposed
        #### 3.1 Primary Technologies
        #### 3.2 Supporting Infrastructure
        
        ### 4. Project Schedule and Milestones
        | Phase | Activity | Start Date | End Date | Deliverable |
        |-------|----------|------------|----------|-------------|
        
        ### 5. Summary Table of Key Deliverables
        | S.No | Deliverable | Specification | Timeline |
        |------|-------------|---------------|----------|
        
        Use **bold** for key deliverables and milestones.
        Cite relevant clauses from the tender (e.g., [Clause 4.2.1]).
        If information is missing, use placeholder: [CLAUSE NOT FOUND - TO BE VERIFIED]
    """,
    "Financial Statements": """
        Identify all financial document requirements from the tender.
        
        MANDATORY OUTPUT FORMAT:
        
        ### Compliance Matrix
        Start with this table (REQUIRED):
        | Clause | Requirement | Compliance Status | Reference |
        |--------|-------------|-------------------|-----------|
        
        Then structure with formal legal numbering:
        
        ### 1. Turnover Requirements
        #### 1.1 Minimum Annual Turnover
        #### 1.2 Average Turnover Requirements
        #### 1.3 Supporting Documents
        
        ### 2. Solvency Certificate Requirements
        #### 2.1 Solvency Amount
        #### 2.2 Issuing Authority
        #### 2.3 Validity Period
        
        ### 3. Bank Guarantee Formats and Values
        #### 3.1 Performance Guarantee
        #### 3.2 Bid Security/EMD
        #### 3.3 Advance Payment Guarantee
        
        ### 4. Earnest Money Deposit (EMD) Methodology
        #### 4.1 EMD Amount
        #### 4.2 Submission Mode
        #### 4.3 Refund Conditions
        
        ### 5. Summary Table of Financial Requirements
        | S.No | Requirement | Amount | Document | Deadline |
        |------|-------------|--------|----------|----------|
        
        Use **bold** for all amounts, percentages, and deadlines.
        If information is missing, use placeholder: [AMOUNT NOT SPECIFIED]
    """,
    "Declarations & Forms": """
        List all mandatory declarations, affidavits, and forms mentioned in the tender.
        
        MANDATORY OUTPUT FORMAT:
        
        ### Compliance Matrix
        Start with this table (REQUIRED):
        | Clause | Requirement | Compliance Status | Reference |
        |--------|-------------|-------------------|-----------|
        
        Then structure with formal legal numbering:
        
        ### 1. Mandatory Declarations
        #### 1.1 Non-Blacklisting Declaration
        #### 1.2 Integrity Pact
        #### 1.3 No Conflict of Interest
        
        ### 2. Affidavits
        #### 2.1 Authorized Signatory Affidavit
        #### 2.2 Financial Status Affidavit
        
        ### 3. Standard Forms
        #### 3.1 Bid Submission Form
        #### 3.2 Technical Bid Form
        #### 3.3 Financial Bid Form
        
        ### 4. Summary Table of Required Documents
        | S.No | Form/Declaration | Purpose | Signatory | Notarization Required |
        |------|------------------|---------|-----------|----------------------|
        
        Use **bold** for form names and signatory requirements.
        If information is missing, use placeholder: [FORM DETAILS NOT FOUND]
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
    parsing_mode: "Fast" (PyMuPDF/PyPDF) or "High-Quality" (LlamaParse Vision with parallelism)
    
    Performance optimizations for large files:
    - Page-Level Parallelism: Splits PDF into 5-page batches for concurrent processing
    - Partial Indexing: Saves index after each batch so generation can start early
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
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        docs = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        
        if parsing_mode == "High-Quality":
            # PARALLEL PARSING FOR LARGE FILES
            print(f"[HIGH-QUALITY] Parsing {file.filename} with LlamaParse (Vision) in parallel...")
            
            # First, get page count using PyPDF to determine batches
            from pypdf import PdfReader, PdfWriter
            reader = PdfReader(temp_path)
            total_pages = len(reader.pages)
            print(f"Total pages: {total_pages}")
            
            BATCH_SIZE = 5  # Process 5 pages at a time
            num_batches = math.ceil(total_pages / BATCH_SIZE)
            
            # Create temporary batch files
            batch_files = []
            for batch_idx in range(num_batches):
                start_page = batch_idx * BATCH_SIZE
                end_page = min((batch_idx + 1) * BATCH_SIZE, total_pages)
                
                writer = PdfWriter()
                for page_num in range(start_page, end_page):
                    writer.add_page(reader.pages[page_num])
                
                batch_path = f"temp_batch_{batch_idx}_{file.filename}"
                with open(batch_path, "wb") as batch_file:
                    writer.write(batch_file)
                batch_files.append((batch_idx, batch_path))
            
            # Parallel parsing function
            def parse_batch(batch_info):
                batch_idx, batch_path = batch_info
                try:
                    parser = LlamaParse(result_type="markdown")
                    batch_docs = parser.load_data(batch_path)
                    result = [Document(
                        page_content=d.text, 
                        metadata={**(d.metadata or {}), "batch": batch_idx}
                    ) for d in batch_docs]
                    os.remove(batch_path)  # Cleanup batch file
                    return result
                except Exception as e:
                    print(f"Batch {batch_idx} failed: {e}")
                    os.remove(batch_path)
                    return []
            
            # Execute parallel parsing with ThreadPoolExecutor
            all_docs = []
            vectorstore = None
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(parse_batch, bf): bf[0] for bf in batch_files}
                
                for future in as_completed(futures):
                    batch_idx = futures[future]
                    try:
                        batch_docs = future.result()
                        all_docs.extend(batch_docs)
                        print(f"[BATCH {batch_idx + 1}/{num_batches}] Parsed {len(batch_docs)} documents")
                        
                        # PARTIAL INDEXING: Save index after each batch
                        if batch_docs:
                            split_docs = text_splitter.split_documents(batch_docs)
                            if vectorstore is None:
                                vectorstore = FAISS.from_documents(split_docs, embeddings)
                            else:
                                batch_vs = FAISS.from_documents(split_docs, embeddings)
                                vectorstore.merge_from(batch_vs)
                            
                            # Save intermediate index
                            vectorstore.save_local(index_path)
                            print(f"[PARTIAL INDEX] Saved after batch {batch_idx + 1}")
                            
                    except Exception as e:
                        print(f"Batch {batch_idx} processing error: {e}")
            
            docs = all_docs
            
        else:
            # 2b. Parse PDF with PyPDFLoader (Local, Fast)
            print(f"Parsing {file.filename} locally...")
            loader = PyPDFLoader(temp_path)
            docs = loader.load()
            
            # 3. Split
            split_docs = text_splitter.split_documents(docs)
            
            # 4. Index & Save
            print("Creating Vector Store...")
            vectorstore = FAISS.from_documents(split_docs, embeddings)
            vectorstore.save_local(index_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "status": "success", 
            "message": f"File indexed successfully ({len(docs)} documents).",
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
    Enhanced with Deep Research (k=15) and Senior Legal Counsel grounding.
    """
    index_path = get_index_path(filename)
    
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Tender document not found. Please upload first.")
    
    try:
        # 1. Load Index
        vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        
        # DEEP RESEARCH: Increased k to 15 for comprehensive context
        retriever = vectorstore.as_retriever(search_kwargs={"k": 15})
        
        # 2. Select Query based on Section
        query = SECTION_PROMPTS.get(section_type, f"Summarize information relevant to {section_type}")
        
        # 3. Retrieve Context (Long-Context approach)
        # NOTE: We don't use "[Document X]" labels as LLM incorrectly cites them
        # Instead, we present raw text and instruct LLM to find actual clause references
        docs = retriever.invoke(query)
        context_text = "\n\n---\n\n".join([d.page_content for d in docs])
        
        # 4. Generate with LLM - SENIOR BID ARCHITECT PROMPT
        system_instruction = f"""
        You are a SENIOR BID ARCHITECT specializing in government tender responses, procurement law, and enterprise proposals.
        Task: Draft the '{section_type}' section for a formal bid response document.
        
        CRITICAL CITATION RULES:
        - Extract and cite ACTUAL clause/article/section numbers from the tender text.
        - Use proper legal citation format: [Article X, Clause Y.Z] or [Section X.Y.Z] or [Clause X.Y]
        - Look for patterns like "Clause 5.2", "Article III", "Section 4.1.3", "Para 6(a)" in the text.
        - If a specific clause number is visible in the text, cite it exactly (e.g., [Clause 5.2.1]).
        - If no clause number is found but content exists, use: [Tender Document - Page/Section Reference]
        - NEVER use generic references like "[Document 1]" or "[Document 5]" - these are invalid.
        
        CRITICAL GROUNDING RULES (FACT-CHECKING):
        - Use STRICTLY the provided context. Do not invent or assume information.
        - If specific information is not found in the context, use placeholder: [DATA NOT FOUND]
        - If amounts or dates are missing, use: [TO BE VERIFIED FROM TENDER DOCUMENT]
        - NEVER hallucinate requirements, clauses, or specifications.
        
        MANDATORY OUTPUT STRUCTURE:
        
        1. **COMPLIANCE MATRIX** (Start every section with this):
           | Clause | Requirement | Compliance Status | Source Reference |
           |--------|-------------|-------------------|------------------|
           Note: "Source Reference" column must contain actual tender clause numbers like [Clause 5.2.1]
        
        2. **HIERARCHICAL NUMBERING** throughout:
           - Use 1.0, 1.1, 1.1.1, 1.1.2, 1.2, 2.0, etc.
           - Main sections: ### 1.0 Section Title
           - Subsections: #### 1.1 Subsection Title
           - Sub-subsections: ##### 1.1.1 Detail
        
        3. **RISK ASSESSMENT TABLE** (Include in every section):
           | Potential Risk | Impact Level | Mitigation Strategy | Owner |
           |----------------|--------------|---------------------|-------|
        
        4. **IMPLEMENTATION TIMELINE** (When applicable):
           | Phase | Activity | Start Date | End Date | Deliverable | Status |
           |-------|----------|------------|----------|-------------|--------|
        
        5. **SUMMARY TABLE OF KEY DELIVERABLES** (End every section with this):
           | S.No | Deliverable | Specification | Deadline | Responsibility |
           |------|-------------|---------------|----------|----------------|
        
        FORMATTING REQUIREMENTS:
        - Output strictly in Markdown format
        - Use H3 (###) for main sections (1.0), H4 (####) for subsections (1.1)
        - Use Markdown Tables (|---|---|) for ALL structured data
        - Use **bold** for requirement headers, amounts, percentages, deadlines
        - Every fact must have a proper citation like [Clause 4.2] or [Section III.5]
        
        TONE: {tone} / Legal / Government-Standard
        - Write in formal, precise legal language
        - Avoid contractions and colloquialisms
        - Be unambiguous and defensible
        
        COMPLIANCE MODE: {'STRICT - Every requirement must have explicit compliance statement' if compliance_mode else 'FLEXIBLE - General compliance overview'}
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"TENDER DOCUMENT CONTENT (extracted from uploaded PDF):\n\n{context_text}\n\n---\n\nBased on the above tender content, draft the '{section_type}' section. Remember to cite actual clause/article numbers from the text, NOT generic document references."}
            ],
            temperature=0.2,  # Lower temperature for more precise legal output
            max_tokens=4096   # Increased for comprehensive sections
        )
        
        return {
            "status": "success",
            "section": section_type,
            "content": response.choices[0].message.content,
            "chunks_used": len(docs)
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
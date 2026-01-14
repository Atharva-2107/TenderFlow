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
import fitz  # PyMuPDF - 15-21x faster than PyPDF
import gc

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

def parse_pdf_fast_quality(file_path: str) -> list:
    """
    HIGH-SPEED QUALITY PDF PARSING using PyMuPDF (fitz).
    - 15-21x faster than PyPDF
    - Superior text extraction with layout awareness
    - Parallel page processing for maximum speed
    - Returns list of LangChain Document objects
    """
    docs = []
    
    try:
        # Open PDF with PyMuPDF
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        print(f"[FAST-QUALITY] Parsing {total_pages} pages with PyMuPDF...")
        
        # Process pages in parallel for maximum speed
        def extract_page(page_num):
            page = pdf_document[page_num]
            # Extract text with layout preservation
            text = page.get_text("text", sort=True)  # sort=True preserves reading order
            return Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "page": page_num + 1,
                    "parser": "pymupdf_fast_quality"
                }
            )
        
        # Use ThreadPoolExecutor for parallel page extraction
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(extract_page, i): i for i in range(total_pages)}
            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    doc = future.result()
                    if doc.page_content.strip():  # Only add non-empty pages
                        docs.append(doc)
                except Exception as e:
                    print(f"[FAST-QUALITY] Page {page_num} extraction error: {e}")
        
        # Sort docs by page number to maintain order
        docs.sort(key=lambda x: x.metadata.get("page", 0))
        
        pdf_document.close()
        print(f"[FAST-QUALITY] Successfully extracted {len(docs)} documents")
        
    except Exception as e:
        print(f"[FAST-QUALITY] Error parsing PDF: {e}")
        # Fallback to PyPDFLoader if PyMuPDF fails
        print("[FAST-QUALITY] Falling back to PyPDFLoader...")
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    
    return docs

def parse_pdf_hybrid_quality(file_path: str) -> list:
    """
    HYBRID HIGH-QUALITY PARSING: Combines PyMuPDF speed with LlamaParse quality.
    
    Strategy:
    1. Use PyMuPDF for instant text extraction (fast)
    2. Detect pages with low text content (likely scanned/image pages)
    3. Only send image-heavy pages to LlamaParse for OCR
    4. Merge results for best of both worlds
    
    This gives:
    - Text-based PDFs: Super fast (PyMuPDF only)
    - Scanned/image PDFs: Quality OCR only where needed (minimal LlamaParse calls)
    """
    import time
    start_time = time.time()
    
    all_docs = []
    pages_needing_ocr = []
    
    try:
        # Step 1: Fast extraction with PyMuPDF
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        print(f"[HYBRID] Phase 1: Fast extraction of {total_pages} pages with PyMuPDF...")
        
        MIN_TEXT_THRESHOLD = 50  # Minimum characters to consider page as "text-based"
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            text = page.get_text("text", sort=True)
            
            # Check if page has images
            image_list = page.get_images(full=True)
            has_images = len(image_list) > 0
            
            # Determine if page needs OCR
            text_length = len(text.strip())
            
            if text_length >= MIN_TEXT_THRESHOLD:
                # Good text extraction - use PyMuPDF result
                all_docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": file_path,
                        "page": page_num + 1,
                        "parser": "pymupdf_hybrid",
                        "text_chars": text_length
                    }
                ))
            elif has_images or text_length < MIN_TEXT_THRESHOLD:
                # Low text + has images = likely scanned page, needs OCR
                pages_needing_ocr.append(page_num)
                # Add placeholder for now
                all_docs.append(Document(
                    page_content=f"[OCR_PENDING_PAGE_{page_num + 1}]",
                    metadata={
                        "source": file_path,
                        "page": page_num + 1,
                        "parser": "pending_llamaparse",
                        "text_chars": text_length
                    }
                ))
        
        pdf_document.close()
        
        phase1_time = time.time() - start_time
        print(f"[HYBRID] Phase 1 complete in {phase1_time:.2f}s - {len(all_docs) - len(pages_needing_ocr)} text pages, {len(pages_needing_ocr)} need OCR")
        
        # Step 2: Send only problematic pages to LlamaParse (if any)
        if pages_needing_ocr:
            print(f"[HYBRID] Phase 2: Sending {len(pages_needing_ocr)} image-heavy pages to LlamaParse...")
            
            try:
                # Extract only the pages that need OCR into a temporary PDF
                from pypdf import PdfReader, PdfWriter
                reader = PdfReader(file_path)
                writer = PdfWriter()
                
                for page_num in pages_needing_ocr:
                    writer.add_page(reader.pages[page_num])
                
                # Save temporary PDF with only OCR-needed pages
                ocr_temp_path = f"temp_ocr_{os.path.basename(file_path)}"
                with open(ocr_temp_path, "wb") as f:
                    writer.write(f)
                
                # Process with LlamaParse
                parser = LlamaParse(result_type="markdown")
                ocr_docs = parser.load_data(ocr_temp_path)
                
                # Map OCR results back to original page numbers
                for i, ocr_doc in enumerate(ocr_docs):
                    if i < len(pages_needing_ocr):
                        original_page = pages_needing_ocr[i]
                        # Find and replace placeholder in all_docs
                        for j, doc in enumerate(all_docs):
                            if doc.metadata.get("page") == original_page + 1 and "pending" in doc.metadata.get("parser", ""):
                                all_docs[j] = Document(
                                    page_content=ocr_doc.text,
                                    metadata={
                                        "source": file_path,
                                        "page": original_page + 1,
                                        "parser": "llamaparse_ocr"
                                    }
                                )
                                break
                
                # Cleanup temp file
                if os.path.exists(ocr_temp_path):
                    os.remove(ocr_temp_path)
                    
                print(f"[HYBRID] Phase 2 complete - OCR processed {len(ocr_docs)} pages")
                
            except Exception as e:
                print(f"[HYBRID] LlamaParse OCR failed: {e}")
                print("[HYBRID] Using PyMuPDF text for all pages (some may have limited text)")
                # Remove placeholder markers
                for i, doc in enumerate(all_docs):
                    if "[OCR_PENDING" in doc.page_content:
                        all_docs[i] = Document(
                            page_content="[Image-based page - text extraction limited]",
                            metadata=doc.metadata
                        )
        
        # Sort by page number
        all_docs.sort(key=lambda x: x.metadata.get("page", 0))
        
        total_time = time.time() - start_time
        print(f"[HYBRID] Complete in {total_time:.2f}s - {len(all_docs)} total documents")
        
        return all_docs
        
    except Exception as e:
        print(f"[HYBRID] Error: {e}")
        print("[HYBRID] Falling back to full LlamaParse...")
        parser = LlamaParse(result_type="markdown")
        llama_docs = parser.load_data(file_path)
        return [Document(page_content=d.text, metadata=d.metadata or {}) for d in llama_docs]

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
            # HYBRID HIGH-QUALITY PARSING
            # Combines PyMuPDF speed with LlamaParse quality for scanned pages
            import time
            start_time = time.time()
            
            print(f"[HIGH-QUALITY HYBRID] Parsing {file.filename}...")
            print("[HIGH-QUALITY HYBRID] Phase 1: Fast extraction with PyMuPDF")
            print("[HIGH-QUALITY HYBRID] Phase 2: OCR for image-heavy pages with LlamaParse")
            
            # Use the hybrid parser
            docs = parse_pdf_hybrid_quality(temp_path)
            
            parse_time = time.time() - start_time
            print(f"[HIGH-QUALITY HYBRID] Parsing complete in {parse_time:.2f}s ({len(docs)} pages)")
            
            # Split and index
            split_docs = text_splitter.split_documents(docs)
            total_chunks = len(split_docs)
            print(f"[HIGH-QUALITY HYBRID] Creating vector store with {total_chunks} chunks...")
            
            # BATCHED INDEXING to prevent memory exhaustion
            EMBED_BATCH_SIZE = 50
            vectorstore = None
            
            for i in range(0, total_chunks, EMBED_BATCH_SIZE):
                batch = split_docs[i:i + EMBED_BATCH_SIZE]
                print(f"[HIGH-QUALITY HYBRID] Indexing chunks {i+1}-{min(i+EMBED_BATCH_SIZE, total_chunks)}/{total_chunks}...")
                
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch, embeddings)
                else:
                    batch_vs = FAISS.from_documents(batch, embeddings)
                    vectorstore.merge_from(batch_vs)
                    del batch_vs
                
                gc.collect()
            
            vectorstore.save_local(index_path)
            total_time = time.time() - start_time
            print(f"[HIGH-QUALITY HYBRID COMPLETE] Index saved with {total_chunks} chunks in {total_time:.2f}s")
            
        else:
            # FAST-QUALITY MODE: Parse PDF with PyMuPDF (15-21x faster than PyPDF)
            import time
            start_time = time.time()
            
            print(f"[FAST-QUALITY MODE] Parsing {file.filename} with PyMuPDF...")
            docs = parse_pdf_fast_quality(temp_path)
            
            parse_time = time.time() - start_time
            print(f"[FAST-QUALITY MODE] Parsing complete in {parse_time:.2f}s ({len(docs)} pages)")
            
            # 3. Split
            split_docs = text_splitter.split_documents(docs)
            total_chunks = len(split_docs)
            
            # 4. BATCHED Index & Save to prevent memory exhaustion
            print(f"[FAST-QUALITY MODE] Creating Vector Store with {total_chunks} chunks...")
            EMBED_BATCH_SIZE = 50
            vectorstore = None
            
            for i in range(0, total_chunks, EMBED_BATCH_SIZE):
                batch = split_docs[i:i + EMBED_BATCH_SIZE]
                print(f"[FAST-QUALITY MODE] Indexing chunks {i+1}-{min(i+EMBED_BATCH_SIZE, total_chunks)}/{total_chunks}...")
                
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch, embeddings)
                else:
                    batch_vs = FAISS.from_documents(batch, embeddings)
                    vectorstore.merge_from(batch_vs)
                    del batch_vs
                
                gc.collect()
            
            vectorstore.save_local(index_path)
            total_time = time.time() - start_time
            print(f"[FAST-QUALITY MODE COMPLETE] Index saved with {total_chunks} chunks in {total_time:.2f}s")
        
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
    compliance_mode: bool = Form(True),
    company_context: str = Form("")
):
    """
    Generates content for a specific section using the pre-built index.
    Enhanced with Deep Research (k=15) and Senior Legal Counsel grounding.
    Now includes company-specific context for personalized tender responses.
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
        
        # 4. Build BIDDER PROFILE with SMART CONTEXT & PRIVACY PROTECTION
        # DEBUG: Log received company context
        print(f"[BACKEND DEBUG] Received company_context: '{company_context}'")
        print(f"[BACKEND DEBUG] company_context length: {len(company_context) if company_context else 0}")
        
        # PRIVACY PROTECTION: Mask sensitive information
        import re
        masked_context = company_context
        if company_context:
            # Mask bank account numbers (show only last 4 digits)
            masked_context = re.sub(
                r'Bank Account Number:\s*(\d+)',
                lambda m: f"Bank Account Number: XXXX-XXXX-{m.group(1)[-4:]}",
                masked_context
            )
            # Mask PAN numbers (show only last 4 characters)
            masked_context = re.sub(
                r'PAN Number:\s*([A-Z0-9]+)',
                lambda m: f"PAN Number: XXXXX{m.group(1)[-4:]}",
                masked_context
            )
            # Mask IFSC codes partially
            masked_context = re.sub(
                r'IFSC Code:\s*([A-Z0-9]+)',
                lambda m: f"IFSC Code: {m.group(1)[:4]}XXXXX",
                masked_context
            )
        
        # SECTION-SPECIFIC RELEVANCE RULES
        section_relevance = {
            "Eligibility Response": ["Company Name", "Turnover", "GST Number"],
            "Technical Proposal": ["Company Name", "Registered Address"],
            "Financial Statements": ["Company Name", "Turnover", "GST Number"],
            "Declarations & Forms": ["Company Name", "Authorized Signatory", "Designation", "GST Number", "PAN Number"]
        }
        
        relevant_fields = section_relevance.get(section_type, ["Company Name"])
        
        bidder_profile_section = ""
        if masked_context and masked_context.strip():
            bidder_profile_section = f"""
        BIDDER COMPANY PROFILE (Reference Only - Use SPARINGLY):
        {masked_context}
        
        SMART USAGE RULES FOR COMPANY DATA:
        1. SECTION-SPECIFIC RELEVANCE: For '{section_type}', only the following are typically needed: {', '.join(relevant_fields)}
        2. DO NOT repeat company details in every paragraph - mention ONCE in the appropriate context
        3. Use company name in headers/titles where a signatory is needed
        4. Use financial figures ONLY in eligibility/financial capacity sections
        5. Use GST/PAN ONLY in declaration sections requiring statutory compliance
        6. If a detail is marked with XXXX (masked), write: "[As per submitted documents]"
        7. NEVER include sensitive banking details in the response body
        8. If a required detail is not provided, use: "[BIDDER TO COMPLETE]"
        """
        
        # 5. Generate with LLM - SENIOR BID ARCHITECT PROMPT
        system_instruction = f"""
        You are a SENIOR BID ARCHITECT specializing in government tender responses, procurement law, and enterprise proposals.
        Task: Draft the '{section_type}' section for a formal bid response document.
        {bidder_profile_section}
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
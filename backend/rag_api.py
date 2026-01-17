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
from ml.trainModel import train_model
import pandas as pd
import xgboost as xgb
import json
from pydantic import BaseModel

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
        # OPTIMIZATION: Limit workers to prevent system freeze
        max_workers = min(4, os.cpu_count() or 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
        # Step 1: Fast extraction with PyMuPDF (Parallel)
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        print(f"[HYBRID] Phase 1: Fast extraction of {total_pages} pages with PyMuPDF...")
        
        MIN_TEXT_THRESHOLD = 50  # Minimum characters to consider page as "text-based"
        
        # Helper function for parallel processing
        def analyze_page(page_num):
            # Re-open doc in thread if needed (PyMuPDF isn't thread-safe for same doc object)
            # But get_text is generally safe if read-only. Safer to use fresh handle if issues arise.
            # For now, we'll try shared handle as it's usually fine for read
            page = pdf_document[page_num]
            text = page.get_text("text", sort=True)
            
            # Check if page has images
            image_list = page.get_images(full=True)
            has_images = len(image_list) > 0
            text_length = len(text.strip())
            
            return {
                "page_num": page_num,
                "text": text,
                "text_length": text_length,
                "has_images": has_images
            }

        # Process pages in parallel
        # Process pages in parallel
        # OPTIMIZATION: Limit workers to prevent system freeze
        max_workers = min(4, os.cpu_count() or 4)
        print(f"[HYBRID] Using {max_workers} workers for page analysis")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(analyze_page, range(total_pages)))
        
        # Sort results by page number
        results.sort(key=lambda x: x["page_num"])
        
        for res in results:
            page_num = res["page_num"]
            text = res["text"]
            text_length = res["text_length"]
            has_images = res["has_images"]
            
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
        # Step 2: Send only problematic pages to LlamaParse (if any)
        if pages_needing_ocr:
            print(f"[HYBRID] Phase 2: Sending {len(pages_needing_ocr)} image-heavy pages to LlamaParse (Parallel Batches)...")
            
            try:
                # Helper to process a batch of pages
                def process_ocr_batch(batch_pages, batch_index):
                    try:
                        from pypdf import PdfReader, PdfWriter
                        reader = PdfReader(file_path)
                        writer = PdfWriter()
                        
                        for p_num in batch_pages:
                            writer.add_page(reader.pages[p_num])
                            
                        batch_temp_path = f"temp_ocr_{os.path.basename(file_path)}_batch_{batch_index}.pdf"
                        with open(batch_temp_path, "wb") as f:
                            writer.write(f)
                            
                        try:
                            parser = LlamaParse(result_type="markdown", fast_mode=False) # Disable fast mode for better quality/reliability
                            batch_docs = parser.load_data(batch_temp_path)
                        except KeyError as e:
                             if str(e) == "'markdown'":
                                 print(f"[HYBRID] Batch {batch_index} LlamaParse KeyError 'markdown' - likely empty response. Falling back to PyMuPDF.")
                                 # Fallback: Try to extract text using PyMuPDF for this batch
                                 try:
                                     fallback_doc = fitz.open(batch_temp_path)
                                     fallback_text = ""
                                     for p in fallback_doc:
                                         fallback_text += p.get_text() + "\n"
                                     fallback_doc.close()
                                     batch_docs = [Document(page_content=fallback_text, metadata={"source": batch_temp_path})]
                                 except Exception as inner_e:
                                      print(f"[HYBRID] Batch {batch_index} fallback failed: {inner_e}")
                                      batch_docs = []
                             else:
                                 raise e
                        
                        # Cleanup
                        if os.path.exists(batch_temp_path):
                            os.remove(batch_temp_path)
                            
                        return batch_docs
                    except Exception as e:
                        print(f"[HYBRID] Batch {batch_index} failed: {e}")
                        return []

                # Split into batches of 20 pages max for parallelism
                BATCH_SIZE = 20
                batches = [pages_needing_ocr[i:i + BATCH_SIZE] for i in range(0, len(pages_needing_ocr), BATCH_SIZE)]
                
                ocr_results = []
                ocr_results = []
                # OPTIMIZATION: Limit concurrent OCR usage to prevent API/System overload
                max_ocr_workers = min(3, os.cpu_count() or 3)
                
                with ThreadPoolExecutor(max_workers=max_ocr_workers) as executor: # Reduced concurrent API calls
                    future_to_batch = {executor.submit(process_ocr_batch, batch, i): batch for i, batch in enumerate(batches)}
                    
                    for future in as_completed(future_to_batch):
                        result_docs = future.result()
                        ocr_results.extend(result_docs)
                
                # Simple mapping: Assuming LlamaParse returns docs in order of pages in the batch PDF
                # We need to be careful. LlamaParse generally preserves order.
                # However, since we batch, we need to map results back to specific page numbers carefully.
                # A safer approach is to trust that `ocr_results` contains text for the pages we sent.
                # But parallel returns are out of order. We need deeper mapping structure.
                
                # REVISED STRATEGY: Map batch results back to logic. 
                # Actually, simpler: LlamaParse returns 1 doc per page usually. 
                # Let's just collect all text and assume we can't perfectly map 1:1 if order scrambles.
                # BUT, wait. LlamaParse `load_data` returns a list of docs.
                # If we process batches, we know which pages were in each batch.
                
                # Rerunning with simpler ordered collection
                all_ocr_docs_ordered = []
                # Rerunning with simpler ordered collection
                all_ocr_docs_ordered = []
                # OPTIMIZATION: Consistent worker count
                with ThreadPoolExecutor(max_workers=max_ocr_workers) as executor:
                    # Submit all batches
                    futures = []
                    for i, batch in enumerate(batches):
                        futures.append(executor.submit(process_ocr_batch, batch, i))
                        
                    # Collect results in order of submission (batches)
                    for future, batch in zip(futures, batches):
                        batch_docs = future.result()
                        # Map these docs to the pages in this batch
                        for i, doc in enumerate(batch_docs):
                            if i < len(batch):
                                original_page = batch[i]
                                all_ocr_docs_ordered.append((original_page, doc.text))

                # Now update the main docs
                for original_page, text in all_ocr_docs_ordered:
                    for j, doc in enumerate(all_docs):
                        # Match page number and pending status
                        if doc.metadata.get("page") == original_page + 1 and "pending" in doc.metadata.get("parser", ""):
                            all_docs[j] = Document(
                                page_content=text,
                                metadata={
                                    "source": file_path,
                                    "page": original_page + 1,
                                    "parser": "llamaparse_ocr_parallel"
                                }
                            )
                            break
                    
                print(f"[HYBRID] Phase 2 complete - OCR processed {len(all_ocr_docs_ordered)} pages")
                
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
    """,
    "Annexures": """
        List all annexures, appendices, and supporting documentation requirements from the tender.
        
        MANDATORY OUTPUT FORMAT:
        
        ### Compliance Matrix
        Start with this table (REQUIRED):
        | Annexure ID | Document Title | Mandatory/Optional | Format | Reference |
        |-------------|----------------|-------------------|--------|----------|
        
        Then structure with formal legal numbering:
        
        ### 1. Technical Annexures
        #### 1.1 Technical Specifications Documents
        Provide exhaustive details on all technical specification documents required. Include format requirements, page limits, mandatory sections, and cross-references.
        #### 1.2 Equipment/Material Datasheets
        Detail all equipment and material datasheets needed, including manufacturer specifications, compliance certificates, and testing reports.
        #### 1.3 Quality Certifications
        List ISO certifications, quality management system certificates, and industry-specific accreditations required.
        #### 1.4 Testing Reports and Compliance Documentation
        Specify all third-party testing reports, lab certifications, and compliance verification documents.
        
        ### 2. Financial Annexures
        #### 2.1 Bill of Quantities (BOQ)
        Provide detailed BOQ format requirements, item categorization, unit pricing structure, and summary totals.
        #### 2.2 Price Schedule Templates
        Detail all price schedule formats including base prices, taxes, duties, escalation clauses, and payment milestones.
        #### 2.3 Financial Guarantee Formats
        Specify bank guarantee formats, performance bond templates, and advance payment guarantee requirements.
        
        ### 3. Legal Annexures
        #### 3.1 Draft Contract/Agreement
        Provide comprehensive analysis of draft contract terms, key clauses, obligations, and acceptance criteria.
        #### 3.2 Terms and Conditions
        Detail general and special conditions of contract, penalty clauses, and force majeure provisions.
        #### 3.3 Dispute Resolution Clauses
        Specify arbitration procedures, jurisdiction, and escalation mechanisms.
        
        ### 4. Reference Documents
        #### 4.1 Sample Work Orders and Previous Experience Documents
        List format requirements for work order citations, client references, and experience certificates.
        #### 4.2 Client Testimonials and Reference Letters
        Specify format and authentication requirements for client references.
        #### 4.3 Organization Chart and Key Personnel CVs
        Detail requirements for organizational structure documentation and personnel qualification formats.
        
        ### 5. Summary Table of Required Annexures
        | S.No | Annexure | Description | Page Limit | Submission Format | Mandatory |
        |------|----------|-------------|------------|-------------------|-----------|   
        
        Use **bold** for annexure titles and mandatory requirements.
        If information is missing, use placeholder: [ANNEXURE DETAILS NOT FOUND]
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
    - IMPORTANT: Provide a COMPREHENSIVE and DETAILED response. 
    - For large documents, ensure you capture ALL key requirements, dates, and eligibility criteria.
    - The summary should be thorough (target 20-25 pages of content, approx 6000-8000 words).
    - BE EXTREMELY DETAILED AND VERBOSE. 
    - Expand on every single point. Do not use summary bullets; use long, detailed paragraphs.
    - Quote specific clauses verbatim where appropriate to add length and precision.
    - Include all specific technical requirements and clause numbers found.
    - Do not leave any section brief. If a section seems short, expand it with relevant context from the tender.
    
    NEGATIVE CONSTRAINTS:
    - Do NOT include any introductory or concluding remarks (e.g., "Here is the analysis...", "Please note...").
    - Do NOT mention the prompt instructions, rules, or guidelines you followed.
    - Output ONLY the requested content directly.
    """

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Context:\n{context_text}\n\nRequest: {user_query}. Please provide a very detailed analysis."}
    ]
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=4500
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
    retriever = vectorstore.as_retriever(search_kwargs={"k": 30}) # Fetch broad context
    
    # 5. Rerank (Optional but recommended)
    try:
        compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, 
            base_retriever=retriever
        )
        # Use the USER QUERY, not a hardcoded one
        print(f"--- Searching for: {query} ---")
        compressed_docs = compression_retriever.invoke(query)[:15]
    except Exception as e:
        print(f"Rerank failed, falling back to standard retrieval: {e}")
        compressed_docs = retriever.invoke(query)[:15]

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
            
            # BATCHED INDEXING to prevent memory exhaustion AND optimize speed
            # OPTIMIZATION: Use add_documents instead of merge_from for O(N) performance vs O(N^2)
            EMBED_BATCH_SIZE = 100 # Increased batch size
            vectorstore = None
            
            for i in range(0, total_chunks, EMBED_BATCH_SIZE):
                batch = split_docs[i:i + EMBED_BATCH_SIZE]
                print(f"[HIGH-QUALITY HYBRID] Indexing chunks {i+1}-{min(i+EMBED_BATCH_SIZE, total_chunks)}/{total_chunks}...")
                
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch, embeddings)
                else:
                    vectorstore.add_documents(batch)
                
                # Aggressive GC to prevent freeze
                if i % (EMBED_BATCH_SIZE * 2) == 0:
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
            # OPTIMIZATION: Use add_documents instead of merge_from
            EMBED_BATCH_SIZE = 100 
            vectorstore = None
            
            for i in range(0, total_chunks, EMBED_BATCH_SIZE):
                batch = split_docs[i:i + EMBED_BATCH_SIZE]
                print(f"[FAST-QUALITY MODE] Indexing chunks {i+1}-{min(i+EMBED_BATCH_SIZE, total_chunks)}/{total_chunks}...")
                
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch, embeddings)
                else:
                    vectorstore.add_documents(batch)
                
                if i % (EMBED_BATCH_SIZE * 2) == 0:
                    gc.collect()
                
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
        # ENHANCED: Increased k to 30 for comprehensive context (18-20 page output)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 30})
        
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
        
        # PRIVACY PROTECTION: Mask sensitive information (if not already hashed by frontend)
        import re
        masked_context = company_context
        if company_context:
            # Mask bank account numbers (show only last 4 digits)
            masked_context = re.sub(
                r'(Bank Account|Account Number):\s*(\d+)',
                lambda m: f"{m.group(1)}: XXXX-XXXX-{m.group(2)[-4:] if len(m.group(2))>=4 else m.group(2)}",
                masked_context
            )
            # Mask PAN numbers (show only last 4 characters)
            masked_context = re.sub(
                r'PAN Number:\s*([A-Z0-9]{5}\d{4}[A-Z])',
                lambda m: f"PAN Number: XXXXX{m.group(1)[-4:]}",
                masked_context
            )
            # Mask IFSC codes partially
            masked_context = re.sub(
                r'IFSC Code:\s*([A-Z]{4}0[A-Z0-9]{6})',
                lambda m: f"IFSC Code: {m.group(1)[:4]}XXXXX",
                masked_context
            )
        
        # SECTION-SPECIFIC RELEVANCE RULES - Aligned with frontend field names
        section_relevance = {
            "Eligibility Response": ["Company Name", "Average Annual Turnover", "FY-wise Turnover", "GST Number", "Past Projects"],
            "Technical Proposal": ["Company Name", "Registered Address", "Past Projects"],
            "Financial Statements": ["Company Name", "Average Annual Turnover", "FY-wise Turnover", "GST Number", "Bank Account", "IFSC Code"],
            "Declarations & Forms": ["Company Name", "Authorized Signatory", "Signatory Designation", "GST Number", "PAN Number", "Registered Address", "Contact Email"],
            "Annexures": ["Company Name", "Past Projects", "Registered Address"]
        }
        
        relevant_fields = section_relevance.get(section_type, ["Company Name"])
        
        bidder_profile_section = ""
        if masked_context and masked_context.strip():
            bidder_profile_section = f"""
        ### BIDDER COMPANY PROFILE (Reference Only)
        PROFILE DATA:
        {masked_context}
        
        ### SMART USAGE RULES FOR BIDDER DATA:
        1. **MINIMALISM (CRITICAL)**: ONLY use profile data if the tender specifically asks for bidder details (e.g., "Company Name", "Financial Capacity", "Signatory").
        2. **SECTION RELEVANCE**: For '{section_type}', typically focus ONLY on: {', '.join(relevant_fields)}. Ignore other fields.
        3. **NO REPETITION**: NEVER repeat the company name or details in every paragraph. Mention once in formal headers or compliance tables only.
        4. **MASKING AWARENESS**: If a detail is masked with '*' or 'X' (e.g., Bank Account: ************3456), write exactly that value or "[As per submitted documents]" in the tender body. NEVER try to guess or hallucinate the full number.
        5. **PROFESSIONAL PLACEMENT**: Use company details primarily in the 'COMPLIANCE MATRIX' and 'SUMMARY' tables where identifying information is mandatory.
        6. **PRIVACY**: Never include sensitive banking or tax details in descriptive technical paragraphs - keep them restricted to structured tables if required.
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
        
        CRITICAL LENGTH REQUIREMENTS (MANDATORY):
        - Generate EXTREMELY DETAILED and COMPREHENSIVE content.
        - Target output: 5000-8000 words per section (approximately 3-4 pages per section).
        - The complete tender document across all 5 sections should total 18-20 pages.
        - DO NOT summarize or be brief. EXPAND on every point with full explanations.
        - Include detailed sub-clauses, explanatory notes, and implementation details.
        - For each requirement, provide: (a) requirement statement, (b) compliance approach, (c) evidence/documentation reference, (d) implementation timeline.
        - Quote specific tender clauses verbatim where available.
        - Add detailed methodology descriptions, step-by-step procedures, and comprehensive explanations.
        - Never leave any section sparse. If content seems short, elaborate further with relevant context.
        - Include executive summaries, detailed breakdowns, cross-references, and dependency mappings.
        - Add explanatory paragraphs before and after each table to provide context.
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"TENDER DOCUMENT CONTENT (extracted from uploaded PDF):\n\n{context_text}\n\n---\n\nBased on the above tender content, draft the '{section_type}' section. Remember to cite actual clause/article numbers from the text, NOT generic document references."}
            ],
            temperature=0.2,  # Lower temperature for more precise legal output
            max_tokens=8000   # Extended for 18-20 page tender sections
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
    depth: str = Form("Standard"),
    parsing_mode: str = Form("Fast")  # NEW: Fast or High-Quality
):
    """
    OPTIMIZED: Uses the same fast parsing + caching strategy as /upload-tender.
    
    parsing_mode:
    - "Fast": PyMuPDF local parsing (15-21x faster)
    - "High-Quality": Hybrid PyMuPDF + LlamaParse OCR for scanned pages
    """
    import time
    start_time = time.time()
    
    try:
        # 1. Check for cached index first
        index_path = get_index_path(file.filename)
        temp_path = None
        
        if os.path.exists(index_path):
            print(f"[ANALYZE-TENDER] Using cached index for {file.filename}")
            vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        else:
            # 2. Save file temporarily for parsing
            temp_path = f"temp_analyze_{file.filename}"
            content = await file.read()
            with open(temp_path, "wb") as buffer:
                buffer.write(content)
            
            # 3. Parse based on mode (same as /upload-tender)
            if parsing_mode == "High-Quality":
                print(f"[ANALYZE-TENDER HIGH-QUALITY] Parsing {file.filename}...")
                docs = parse_pdf_hybrid_quality(temp_path)
            else:
                print(f"[ANALYZE-TENDER FAST] Parsing {file.filename} with PyMuPDF...")
                docs = parse_pdf_fast_quality(temp_path)
            
            parse_time = time.time() - start_time
            print(f"[ANALYZE-TENDER] Parsing complete in {parse_time:.2f}s ({len(docs)} pages)")
            
            # OPTIMIZATION: Chunk size 2000 (~400-500 tokens) is the sweet spot for speed/quality
            # Parallelize splitting to utilize multi-core CPU
            chunk_size = 2000
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=200)
            
            # Helper for parallel splitting
            def split_doc_batch(batch_docs):
                splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=200)
                return splitter.split_documents(batch_docs)
            
            # Split docs into batches for workers
            import itertools
            split_workers = min(4, os.cpu_count() or 4)
            # Create sub-lists of documents
            doc_batches = [docs[i::split_workers] for i in range(split_workers)]
            doc_batches = [b for b in doc_batches if b] # Remove empty
            
            print(f"[ANALYZE-TENDER] Splitting {len(docs)} pages using {len(doc_batches)} threads...")
            split_docs = []
            
            with ThreadPoolExecutor(max_workers=split_workers) as executor:
                results = executor.map(split_doc_batch, doc_batches)
                for res in results:
                    split_docs.extend(res)
                    
            print(f"[ANALYZE-TENDER] Split into {len(split_docs)} chunks")
            
            # 5. Create VectorStore (Batched)
            # Increased batch size to 100 for faster parallel embedding
            batch_size = 100 
            vectorstore = FAISS.from_documents(split_docs[:batch_size], embeddings)
            if len(split_docs) > batch_size:
                for i in range(batch_size, len(split_docs), batch_size):
                    batch = split_docs[i:i + batch_size]
                    # OPTIMIZATION: Use add_documents instead of add_documents loop
                    vectorstore.add_documents(batch)
                    print(f"  - Processed batch {i//batch_size} of {len(split_docs)//batch_size}")
                    
                    if i % (batch_size * 2) == 0:
                        gc.collect()
            gc.collect() # Ensure memory is cleared after large operations
            
            # 6. Cache the index for future use
            vectorstore.save_local(index_path)
            print(f"[ANALYZE-TENDER] Index cached at {index_path}")
        
        # 7. Retrieve context (same strategy as /generate-section)
        k_value = 15 if depth == "Deep Dive" else 10
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_value})
        
        # 8. Optional reranking
        try:
            compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=retriever
            )
            compressed_docs = compression_retriever.invoke(query)[:5]
        except Exception as e:
            print(f"[ANALYZE-TENDER] Rerank failed, using standard retrieval: {e}")
            compressed_docs = retriever.invoke(query)[:5]
        
        # 9. Generate summary with Groq
        result = generate_summary_with_groq(query, compressed_docs, output_format)
        
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        total_time = time.time() - start_time
        print(f"[ANALYZE-TENDER COMPLETE] Total time: {total_time:.2f}s")
        
        return {
            "status": "success",
            "summary": result,
            "processing_time": f"{total_time:.2f}s",
            "cached": os.path.exists(index_path)
        }
        
    except Exception as e:
        print(f"[ANALYZE-TENDER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }

# --- AI MODEL SERVING ---
model = None
feature_columns = None

def load_ai_model():
    global model, feature_columns
    try:
        model = xgb.Booster()
        # Use absolute path or relative to execution dir
        model.load_model("ml/tenderflow_xgboost.json")
        with open("ml/feature_columns.json", "r") as f:
            feature_columns = json.load(f)
        print("✅ AI Model loaded successfully")
    except Exception as e:
        print(f"⚠️ Model load failed (using fallback): {e}")
        model = None

class PredictRequest(BaseModel):
    prime_cost_lakh: float
    overhead_pct: float
    profit_pct: float
    estimated_budget_lakh: float
    complexity_score: int
    competitor_density: int

@app.post("/predict-win")
async def predict_win(data: PredictRequest):
    global model, feature_columns
    
    if not model:
        load_ai_model()
    
    if not model:
         # Fallback if model still not loaded (e.g. no training data yet)
         print("Model not available, returning default")
         return {"win_probability": 0.5, "note": "Model not loaded"}

    try:
        # Prepare inputs matching training features
        # Training used: prime_cost, overhead_pct, profit_pct, complexity_score, competitor_density
        # Note: estimated_budget is ignored as per training data availability
        input_dict = {
            "prime_cost": data.prime_cost_lakh,
            "overhead_pct": data.overhead_pct,
            "profit_pct": data.profit_pct,
            "complexity_score": data.complexity_score,
            "competitor_density": data.competitor_density
        }
        
        # Ensure DataFrame aligns with feature columns
        df = pd.DataFrame([input_dict])
        
        # Add missing cols if any (robustness)
        for c in feature_columns:
            if c not in df.columns:
                df[c] = 0
                
        # Reorder
        df = df[feature_columns]
        
        dtest = xgb.DMatrix(df)
        preds = model.predict(dtest)
        prob = float(preds[0])
        return {"win_probability": prob}
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"win_probability": 0.5}

@app.post("/retrain-model")
async def retrain_model_endpoint():
    """Trigger the XGBoost model retraining process using latest Supabase data"""
    try:
        # Run training synchronously (can be background task for scalability)
        success = train_model()
        if success:
            # RELOAD MODEL IN MEMORY
            load_ai_model()
            return {"status": "success", "message": "Model retrained and reloaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Training returned False")
    except Exception as e:
        print(f"Retraining Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
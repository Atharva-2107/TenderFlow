import os
from dotenv import load_dotenv
from flashrank import Ranker
from groq import Groq  # 🧠 The Brain
from llama_parse import LlamaParse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import FlashrankRerank
from langchain_core.documents import Document

load_dotenv()

# --- NEW: Initialize Groq Client ---
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_summary_with_groq(user_query, retrieved_chunks):
    """
    Sends the top ranked chunks to Llama-3.3 on Groq for a final answer.
    """
    print(f"\n🧠 GENERATING: Sending {len(retrieved_chunks)} chunks to Llama-3.3...")
    
    # 1. Combine all chunk text into one big context block
    context_text = "\n\n".join([doc.page_content for doc in retrieved_chunks])
    
    # 2. Build the Strict Prompt
    system_prompt = """
    You are a Senior Technical Tender Analyst. Your job is to extract precise information 
    from the provided tender documents to answer the user's question.
    
    Rules:
    - Answer ONLY based on the provided Context.
    - If the answer is not in the context, say "Data not found in the provided documents."
    - Be detailed and professional. Use bullet points where appropriate.
    - Cite specific section names or page numbers if available in the text.
    """
    
    user_prompt = f"""
    Context Data:
    {context_text}
    
    User Question: 
    {user_query}
    
    Provide a detailed, structured response:
    """

    # 3. Call Groq API
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile", # The big gun model
        temperature=0.3, # Keep it factual, low creativity
    )
    
    return chat_completion.choices[0].message.content

def advanced_rag_pipeline(pdf_path):
    # 1. High-Fidelity Parsing
    print(f"\n1️⃣  STARTING: Parsing {pdf_path}...")
    parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY"), result_type="markdown")
    llama_docs = parser.load_data(pdf_path)
    
    # Conversion Step (Llama -> LangChain)
    langchain_docs = [
        Document(page_content=d.text, metadata=d.metadata or {}) 
        for d in llama_docs
    ]
    print(f"✅ PARSED. Converted {len(langchain_docs)} pages to LangChain format.")

    # 2. Smart Chunking (Recursive) -> BIGGER CHUNKS
    print("\n2️⃣  STARTING: Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(langchain_docs)
    print(f"✅ CHUNKED. Created {len(docs)} chunks.")

    # 3. Local Vector Engine (FastEmbed + FAISS)
    print("\n3️⃣  STARTING: FastEmbed (Indexing)...")
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    vectorstore = FAISS.from_documents(docs, embeddings)
    print("✅ INDEXED. Vector Database created in memory.") # <--- Added Tick Mark!

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20}) # Increased to 30

    # 4. Advanced Reranking (Contextual Compression)
    print("\n4️⃣  STARTING: FlashRank (Reranking)...")
    compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, 
        base_retriever=base_retriever
    )

    # 5. Execution
    query = "What is Financial Management."
    print(f"\n🔎 SEARCHING for: '{query}'")
    
    # Get top 5 highly relevant chunks (Increased from 3)
    compressed_docs = compression_retriever.invoke(query)[:5]
    print(f"✅ RETRIEVAL COMPLETE. Found {len(compressed_docs)} Gold Chunks.")
    
    # 6. Final Generation (Groq)
    final_answer = generate_summary_with_groq(query, compressed_docs)
    
    print("\n" + "="*50)
    print("🤖 FINAL GENERATED ANSWER:")
    print("="*50)
    print(final_answer)
    print("="*50)
    
    return final_answer

if __name__ == "__main__":
    test_file = "sample_tender.pdf"
    if os.path.exists(test_file):
        advanced_rag_pipeline(test_file)
    else:
        print(f"❌ ERROR: File '{test_file}' not found.")
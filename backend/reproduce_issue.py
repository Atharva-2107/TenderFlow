
import os
import sys
from dotenv import load_dotenv
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def reproduce():
    print("Attempting to reproduce KeyError: 'markdown'...")
    pdf_path = os.path.join(os.path.dirname(__file__), "sample_tender.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        # Create a dummy pdf for testing
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="This is a test tender document.", ln=1, align="C")
            pdf.output(pdf_path)
            print(f"Created dummy PDF at {pdf_path}")
        except Exception as e:
            print(f"Failed to create dummy PDF: {e}")
            return

    try:
        from llama_parse import LlamaParse
        
        print(f"Parsing {pdf_path} using LlamaParse...")
        # Replicating the call from rag_api.py
        # Try WITHOUT fast_mode first to see if it works, then WITH fast_mode
        
        print("--- TEST 1: fast_mode=True (Original) ---")
        try:
            parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY"), result_type="markdown", fast_mode=True)
            llama_docs = parser.load_data(pdf_path)
            print(f"Success! Docs: {len(llama_docs)}")
        except Exception:
            traceback.print_exc()

        print("\n--- TEST 2: fast_mode=False (Standard) ---")
        try:
            parser_slow = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY"), result_type="markdown", fast_mode=False)
            docs_slow = parser_slow.load_data(pdf_path)
            print(f"Success! Docs: {len(docs_slow)}")
        except Exception:
            traceback.print_exc()
    except ImportError:
        print("llama_parse not installed!")
    except Exception as e:
        print(f"Top level error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()

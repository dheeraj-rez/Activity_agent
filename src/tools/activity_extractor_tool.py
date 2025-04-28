import os
import fitz  # PyMuPDF 
import numpy as np
import json
# import faiss # Uncomment if you want to use FAISS for vector store
from src.tools.clients import openai_client, mistral_client
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def need_ocr(pdf_path: str, pages_to_check: int = 5) -> bool:
    """
    Return True if the first `pages_to_check` pages contain fewer than
    MIN_CHARS_PER_PAGE characters each (likely image‑only).
    """
    minimum_chars_per_page = 50
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(pages_to_check, len(doc))):
            page = doc[i]
            text = page.get_text("text").strip()
            if len(text) > minimum_chars_per_page:
                return False
        doc.close()
        print(f"🚨 PDF likely contains images only. OCR is required for {pdf_path}.")
        return True
    except Exception as e:
        print(f"🚨 Error checking PDF for OCR: {e}")
        return False

def get_pdf_signed_url(pdf_path: str) -> str:
    """
    Upload a PDF to Mistral's file store for OCR and return the signed URL.
    """
    if not os.path.exists(pdf_path):
        print(f"🚨 PDF file not found: {pdf_path}")
        return None
    
    print("Uploading PDF to Mistral's file store for OCR...")
    
    with open(pdf_path, "rb") as f:
        uploaded = mistral_client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": f,
            },
            purpose="ocr"
        )
    if not uploaded:
        print("🚨 Failed to upload PDF to Mistral's file store.")
        return None
    
    url = mistral_client.files.get_signed_url(file_id=uploaded.id).url
    print(f"🚀 PDF uploaded successfully. Signed URL: {url}")
    return url

def extract_text_with_mistral(url: str) -> dict:
    """Extract text from a PDF with images using Mistral AI OCR, using sequential page numbering."""

    if not mistral_client:
        print("🚨 Mistral client not initialized. Check your API key.")
        return {}

    pages = {}
    try:
        if not url:
            print("🚨 No URL provided for Mistral OCR.")
            return {}
        
        ocr_response = mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": url}
        )

        if not hasattr(ocr_response, 'pages') or not ocr_response.pages:
            print("🚨 OCR response has no 'pages' attribute or it's empty.")
            return {}

        for page in ocr_response.pages:
            page_number = page.index + 1
            raw_text = page.markdown if page.markdown is not None else ""
            stripped_text = raw_text.strip()
            if not stripped_text:
                print(f"Warning: Page {page_number} has no meaningful text after stripping (raw: '{raw_text}')")
            pages[page_number] = stripped_text if stripped_text else ""

        if not pages:
            print("🚨 No pages extracted from OCR response.")
        else:
            print(f"Extracted text from {len(pages)} image-based pages using Mistral OCR with sequential numbering.")
        return pages
    except Exception as e:
        print(f"🚨 Error using Mistral AI OCR: {str(e)}")
        return {}

def extract_text_with_pymupdf(pdf_path: str) -> dict:
    """Extract text from a text-based PDF using PyMuPDF, using sequential page numbers."""
    pages = {}
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            page_number = i + 1
            pages[page_number] = text if text else ""
        doc.close()
        print(f"Extracted text from {len(pages)} text-based pages using PyMuPDF with sequential numbering.")
        return pages
    except Exception as e:
        print(f"🚨 Error using PyMuPDF: {str(e)}")
        return {}

def get_embedding(text):
    """Generate OpenAI embedding for a given text."""
    if not openai_client:
        print("🚨 OpenAI client not initialized. Check your API key.")
        return None
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text[:8192]
        )
        return np.array(response.data[0].embedding)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def build_vector_store(pages):
    """Create FAISS vector store for textbook pages."""
    dimension = 1536
    # Uncomment the following line if you want to use indexing
    # index = faiss.IndexFlatL2(dimension)
    index = None
    text_data = []
    
    for page, text in pages.items():
        if not text.strip():
            print(f"Skipping embedding for page {page} due to empty text")
            text_data.append({"page": page, "text": text})
            continue
        # Uncomment the following line if you want to use embeddings
        # embedding = get_embedding(text)
        embedding = True
        if embedding is not None:
            # index.add(np.array([embedding], dtype=np.float32))
            text_data.append({"page": page, "text": text})
    
    return index, text_data

def extract_activity_details(text:str, page_numbers:list) -> list:
    """Use GPT to extract structured activity details from a chunk of pages."""
    prompt = f"""
    You are analyzing a school textbook to extract class activities which could be performed in the ongoing class.

    Activity should be like a student can perform it in the live classroom by which some concepts could be understood.

    Search the keywords like: 
    "Activity", "Let us do", "Let us perform", "Let us explore", "Think like a scientist", "Activity 1.1", "Activity 2.1" etc.

    These all keywords are used to identify the activities in the text.
    The text includes page markers in the format 'Page X:' where X is the page number. Use these markers to determine the exact page(s) where each activity appears.

    For each activity, identify:
    1. **Activity Name**
    2. **Concept being taught**
    3. **Materials required**
    4. **Short description of how to perform the activity**
    5. **Page number(s)** (provided as a list of page numbers: {page_numbers})
    💡 **Example Output Format (JSON), return valid JSON only**:
    [
        {{
            "activity": "Activity 4.1: Let us explore",
            "concept": "Magnetic and Non-Magnetic Materials",
            "materials": ["Magnet", "Various objects"], 
            "description": "Step-by-step process to perform the activity",
            "page": [41]
        }}
    ]

    Output should only be JSON and no any other explanations.

    Extract relevant details from the following text:
    \"\"\"{text}\"\"\"
    """

    if not openai_client:
        print("🚨 OpenAI client not initialized. Check your API key.")
        return []

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Extract structured details from textbook activities."},
                  {"role": "user", "content": prompt}],
        temperature=0
    )
    try:
        result = json.loads(response.choices[0].message.content)
        # print(f"GPT-4 response for page numbers {page_numbers}: {result}")  # Debug
        # Ensure page field matches the provided list or subset
        for activity in result:
            if "page" not in activity or activity["page"] is None:
                activity["page"] = page_numbers
        return result
    except json.JSONDecodeError as e:
        print(f"JSON decode error for page numbers {page_numbers}: {e}")
        return []

def search_activity(index, text_data) -> list:
    """Search for activities in chunks of 10 pages."""
    results = []
    chunk_size = 10
    for i in range(0, len(text_data), chunk_size):
        end_idx = min(i + chunk_size, len(text_data))
        chunk = text_data[i:end_idx]
        
        # Add page markers to the text
        marked_text = "\n\n".join([f"Page {item['page']}: {item['text']}" for item in chunk])
        # Get list of page numbers for the chunk
        page_numbers = [item["page"] for item in chunk]
        
        print(f"Processing chunk for page numbers {page_numbers}")
        # Check for activity keywords in the chunk
        activity_keywords = ["activity", "let us do", "let us perform", "let us explore", 
                           "think like a scientist", "activity 1.1", "activity 2.1"]
        if any(keyword in marked_text.lower() for keyword in activity_keywords):
            activity_details = extract_activity_details(marked_text, page_numbers)
            results.extend(activity_details)
    
    return results

def save_results_to_json(results: list, file_name: str = "activities.json", output_dir: str = r"D:\Python\LangChain-Tutorial\Activity_agent\output") -> str:
    """Save results to JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)  
    
    if not results:
        print("🚨 No results to save.")
        return "No results to save."

    out_path = output_dir / file_name

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    return f"Results saved to {out_path}"

def extract_activities_from_pdf(pdf_path: str = None) -> str:
    """
    Extract activities from a PDF file and save them to a JSON file.    
    """
    if pdf_path is None:
        print("🚨 No PDF path provided.")
        return "Please provide a valid PDF file path."
    
    if not os.path.exists(pdf_path):
        print(f"🚨 PDF file not found: {pdf_path}")
        return "Pdf file not found at the specified path."

    if not pdf_path.lower().endswith('.pdf'):
        print(f"🚨 Invalid file type: {pdf_path}. Only PDF files are supported.")
        return "Invalid file type. Only PDF files are supported."

    # Check if OCR is needed based on the PDF content
    use_ocr = need_ocr(pdf_path)

    if use_ocr:
        doc_url = get_pdf_signed_url(pdf_path)
        if not doc_url:
            print("🚨 Failed to get signed URL for OCR processing.")
            return "Failed to get signed URL for OCR processing."
        else:
            pages = extract_text_with_mistral(doc_url)
            output_dir = Path(r"D:\Python\LangChain-Tutorial\Activity_agent\output")
            file_name = "activities.json"
    else:
        pages = extract_text_with_pymupdf(pdf_path)

    if not pages:
        print("🚨 No pages extracted from the PDF.")
        return "No pages extracted from the PDF."
    
    index, text_data = build_vector_store(pages)
    if text_data is None:
        print("🚨 Failed to build vector store.")
        return "Failed to build vector store."
    
    activities = search_activity(index, text_data)
    output_dir = Path(pdf_path).resolve().parent
    file_name = Path(pdf_path).stem + "_activities.json"

    if not activities:
        print("🚨 No activities found in the PDF.")
        return "No activities found in the PDF."
    else:
        print(f"Found {len(activities)} activities in the PDF.")
        save_results = save_results_to_json(activities, file_name, output_dir)
        print(save_results)
        return save_results
    
if __name__ == "__main__":
    pdf_path = r"C:\Users\LPT029\Downloads\CLS_7.pdf"
    extract_activities_from_pdf(pdf_path)

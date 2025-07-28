# src/main.py

import pdfplumber
import json
import re
from datetime import datetime
import os
import sys
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# --- Define I/O Directories ---
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

# --- Helper Functions (Unchanged from your original script) ---

def extract_text_from_pdf(pdf_path):
    """Extracts text page by page from a PDF."""
    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_text.append({"page_number": i + 1, "text": text})
        return pages_text
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}", file=sys.stderr)
        return []

def preprocess_text(text):
    """Converts text to lowercase and removes non-alphanumeric characters."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def get_keywords(description):
    """Extracts keywords from a description, removing common stop words."""
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(description.lower())
    keywords = [word for word in words if word.isalnum() and word not in stop_words]
    return set(keywords)

def calculate_relevance_score(text, keywords):
    """Calculates a simple relevance score based on keyword density."""
    if not text or not keywords:
        return 0.0
    processed_text = preprocess_text(text)
    text_words = word_tokenize(processed_text)
    if not text_words:
        return 0.0
    unique_matched_in_block = {word for word in text_words if word in keywords}
    return len(unique_matched_in_block) / len(text_words)

def get_section_title_from_text(text, max_length=100):
    """Attempts to derive a section title from the first sentence or prominent line."""
    if not text:
        return "Untitled Section"
    first_line = text.strip().split('\n')[0].strip()
    if first_line:
        if len(first_line) > max_length:
            return first_line[:max_length].rsplit(' ', 1)[0] + "..."
        return first_line
    return "Relevant Content"

# --- Main Logic Function ---

def intelligent_document_analyst(document_path, persona_description, job_to_be_done):
    all_extracted_content = []
    doc_name = os.path.basename(document_path)
    pages_data = extract_text_from_pdf(document_path)
    
    for page_data in pages_data:
        paragraphs = [p.strip() for p in page_data["text"].split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [page_data["text"].strip()]

        for para_idx, paragraph_text in enumerate(paragraphs):
            if paragraph_text:
                all_extracted_content.append({
                    "document": doc_name,
                    "page_number": page_data["page_number"],
                    "text_content": paragraph_text,
                    "paragraph_index": para_idx
                })

    persona_keywords = get_keywords(persona_description)
    job_keywords = get_keywords(job_to_be_done)
    combined_keywords = persona_keywords.union(job_keywords)
    
    scored_content = []
    for item in all_extracted_content:
        score = calculate_relevance_score(item["text_content"], combined_keywords)
        if score > 0:
            item['score'] = score
            scored_content.append(item)
            
    scored_content.sort(key=lambda x: x["score"], reverse=True)

    output_sections = []
    output_sub_sections = []
    
    max_sections_to_output = 10
    for i, item in enumerate(scored_content[:max_sections_to_output]):
        output_sections.append({
            "document": item["document"],
            "page_number": item["page_number"],
            "section_title": get_section_title_from_text(item["text_content"]),
            "importance_rank": i + 1
        })
        output_sub_sections.append({
            "document": item["document"],
            "page_number": item["page_number"],
            "refined_text": item["text_content"]
        })

    return {
        "metadata": {
            "input_document": doc_name,
            "persona": persona_description,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": output_sections,
        "sub_section_analysis": output_sub_sections
    }

# --- Container Execution Block ---

if __name__ == "__main__":
    print("Container started. Analyst script is running.")
    
    # Read persona and job from environment variables. Provide defaults for safety.
    persona = os.getenv("PERSONA_DESCRIPTION", "Default persona: a general researcher")
    job = os.getenv("JOB_TO_BE_DONE", "Default job: find the most relevant sections")
    
    print(f"Using Persona: '{persona}'")
    print(f"Using Job To Be Done: '{job}'")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in '{INPUT_DIR}'. Exiting.")
        sys.exit(0)
        
    for filename in pdf_files:
        input_path = os.path.join(INPUT_DIR, filename)
        output_filename = os.path.splitext(filename)[0] + ".json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        print(f"Processing '{filename}'...")
        
        try:
            analysis_result = intelligent_document_analyst(input_path, persona, job)
            
            with open(output_path, 'w') as f:
                json.dump(analysis_result, f, indent=4)
                
            print(f"-> Successfully generated '{output_filename}'")
        except Exception as e:
            print(f"!! Failed to process '{filename}': {e}", file=sys.stderr)

    print("\nAll files processed. Container finished.")
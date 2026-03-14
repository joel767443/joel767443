#!/usr/bin/env python3
# CV Extractor Script - Saves structured data from any CV PDF to JSON
# Uses pyresparser (offline NLP parser for resumes/CVs).
# Extracts: name, email, phone, skills, experience (dates/titles/companies), education, etc.
#
# INSTALL ONCE (run in terminal):
#   pip install -r requirements.txt   # includes pyresparser and spacy 2.x
#   python -m spacy download en_core_web_sm   # after spacy 2.x: use compatible model
#   If "en_core_web_sm" is for spaCy 3, install 2.x model instead:
#     pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.1/en_core_web_sm-2.3.1.tar.gz
#   python -c "import nltk; nltk.download('stopwords')"

import argparse
import io
import json
import re
from pathlib import Path

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

# Ensure NLTK stopwords available (pyresparser dependency)
def _ensure_nltk_stopwords():
    try:
        from nltk.corpus import stopwords
        stopwords.words("english")
    except LookupError:
        import nltk
        nltk.download("stopwords", quiet=True)


_ensure_nltk_stopwords()

from pyresparser import ResumeParser


def extract_raw_text_from_pdf(pdf_path) -> str:
    """Extract raw text from PDF (preserves paragraph breaks)."""
    pdf_path = Path(pdf_path)
    text_parts = []
    with open(pdf_path, "rb") as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            resource_manager = PDFResourceManager()
            out = io.StringIO()
            converter = TextConverter(
                resource_manager, out, codec="utf-8", laparams=LAParams()
            )
            interpreter = PDFPageInterpreter(resource_manager, converter)
            interpreter.process_page(page)
            text_parts.append(out.getvalue())
            converter.close()
            out.close()
    return "\n".join(text_parts)


def extract_summary_from_text(full_text: str) -> str:
    """
    Find a Summary/Objective/Profile section in CV text and return it.
    Returns multiple paragraphs joined by newlines; if no section found, use first substantive paragraphs.
    """
    if not full_text or not full_text.strip():
        return ""
    # Normalize: collapse multiple newlines to double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", full_text.strip())
    lines = [ln.strip() for ln in text.split("\n")]
    # Build paragraphs (blocks of non-empty lines)
    paragraphs = []
    current = []
    for line in lines:
        if line:
            current.append(line)
        else:
            if current:
                paragraphs.append(" ".join(current))
                current = []
    if current:
        paragraphs.append(" ".join(current))

    # Section headers that typically introduce a summary (case-insensitive)
    summary_headers = (
        "summary", "objective", "profile", "about me", "about",
        "professional summary", "overview", "key highlights", "executive summary",
        "career summary", "personal statement", "introduction"
    )
    # Section headers that usually follow the summary (stop here)
    stop_headers = (
        "experience", "work experience", "employment", "education",
        "qualifications", "skills", "technical skills", "certifications",
        "projects", "references", "contact"
    )

    def is_header(line, header_set):
        line_lower = line.lower().strip()
        if not line_lower or len(line_lower) > 60:
            return False
        # Exact or line starts with header (e.g. "Professional Summary")
        for h in header_set:
            if line_lower == h or line_lower.startswith(h + ":") or line_lower.startswith(h + " "):
                return True
        # All-caps short line often a section title
        if line_lower.isupper() and len(line_lower) < 35:
            return any(h in line_lower for h in header_set)
        return False

    summary_paragraphs = []
    found_header = False
    for i, para in enumerate(paragraphs):
        if is_header(para, stop_headers) and found_header:
            break
        if is_header(para, summary_headers):
            found_header = True
            continue
        if found_header:
            if len(para) < 20:
                continue
            summary_paragraphs.append(para)
            if len(summary_paragraphs) >= 5:
                break
            # Stop after a reasonable length (e.g. 1200 chars) to avoid cutting mid-sentence
            if sum(len(p) for p in summary_paragraphs) >= 1200:
                break

    if summary_paragraphs:
        return "\n\n".join(summary_paragraphs)

    # Fallback: first 1–2 substantive paragraphs (not just name/email)
    for para in paragraphs[:5]:
        if len(para) >= 80 and not re.match(r"^[\w\s\.\-@]+$", para):
            summary_paragraphs.append(para)
            if len(summary_paragraphs) >= 2:
                break
    return "\n\n".join(summary_paragraphs) if summary_paragraphs else ""


def get_default_paths():
    """Resolve default PDF and output paths from project root."""
    project_root = Path(__file__).resolve().parent.parent
    return (
        project_root / "scripts" / "cv.pdf",
        project_root / "data" / "cv_extracted.json",
    )


def extract_cv_to_json(pdf_path: str, output_json: str = None) -> dict:
    """
    Extracts data from the CV PDF and saves it as clean JSON.
    Works with standard CVs (name, email, skills, experience, education, etc.).
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"CV PDF not found: {pdf_path}")

    if output_json is None:
        _, output_json = get_default_paths()
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Extracting data from: {pdf_path}")
    extracted_data = ResumeParser(str(pdf_path)).get_extracted_data()

    # Extract summary from raw PDF text (Summary/Objective/Profile section or first paragraphs)
    raw_text = extract_raw_text_from_pdf(pdf_path)
    summary = extract_summary_from_text(raw_text)
    if summary:
        extracted_data["summary"] = summary

    # Preserve structured entries if they exist in the output file (don't overwrite with flat data)
    if output_path.exists():
        try:
            with open(output_path, encoding="utf-8") as f:
                existing = json.load(f)
            for key in ("experience_entries", "education", "certifications"):
                if key in existing and existing[key]:
                    extracted_data[key] = existing[key]
        except (json.JSONDecodeError, OSError):
            pass

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    print(f"Successfully saved to {output_path}")
    preview = json.dumps(extracted_data, indent=2)[:1000]
    print("\nPreview of extracted data:")
    print(preview + ("..." if len(preview) >= 1000 else ""))

    return extracted_data


def main():
    default_pdf, default_json = get_default_paths()
    parser = argparse.ArgumentParser(
        description="Extract structured data from a CV PDF and save to JSON."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=str(default_pdf),
        help=f"Path to CV PDF (default: {default_pdf})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(default_json),
        help=f"Output JSON path (default: {default_json})",
    )
    args = parser.parse_args()

    data = extract_cv_to_json(args.pdf, args.output)

    print("\n=== QUICK SUMMARY ===")
    print("Name:", data.get("name"))
    print("Email:", data.get("email"))
    print("Skills count:", len(data.get("skills", [])))
    print("Experience entries:", len(data.get("experience", [])))


if __name__ == "__main__":
    main()

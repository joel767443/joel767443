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
import json
from pathlib import Path

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

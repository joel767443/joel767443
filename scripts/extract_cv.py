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


def _is_continuation_line(line: str, prev_line: str) -> bool:
    """True if this line is likely a continuation (line wrap) of the previous line."""
    if not line or not prev_line:
        return False
    # Next line starts with lowercase -> continuation
    if line[0].islower():
        return True
    # Short line that doesn't look like a new sentence (no period at end of prev)
    if len(line) < 50 and prev_line.rstrip() and prev_line.rstrip()[-1] not in ".!?":
        return True
    # Line is just a fragment like "systems," or "overhead through automation"
    if len(line) < 60 and not line.endswith(".") and not line.endswith("!") and not line.endswith("?"):
        return True
    return False


def extract_summary_from_text(full_text: str) -> str:
    """
    Find a Summary/Objective/Profile section in CV text and return it.
    Merges PDF line wraps into full paragraphs; stops at Experience/Education etc.
    """
    if not full_text or not full_text.strip():
        return ""
    text = re.sub(r"\n{3,}", "\n\n", full_text.strip())
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    summary_headers = (
        "summary", "objective", "profile", "about me", "about",
        "professional summary", "overview", "key highlights", "executive summary",
        "career summary", "personal statement", "introduction"
    )
    stop_headers = (
        "experience", "work experience", "employment", "education",
        "qualifications", "skills", "technical skills", "certifications",
        "projects", "references", "contact", "page 1 of", "page 2 of"
    )

    def is_header(line: str, header_set) -> bool:
        line_lower = line.lower().strip()
        if not line_lower or len(line_lower) > 70:
            return False
        for h in header_set:
            if line_lower == h or line_lower.startswith(h + ":") or line_lower.startswith(h + " "):
                return True
        if line_lower.isupper() and len(line_lower) < 40:
            return any(h in line_lower for h in header_set)
        return False

    # Find start of summary section (line index after the summary header)
    start_idx = None
    for i, line in enumerate(lines):
        if is_header(line, summary_headers):
            start_idx = i + 1
            break
    if start_idx is None:
        # Fallback: use first substantive block (skip contact/name lines)
        for i, line in enumerate(lines):
            if len(line) >= 100 and not re.match(r"^[\w\s\.\-@:/]+$", line):
                start_idx = i
                break
        if start_idx is None:
            return ""

    # Collect lines until we hit a stop header or an all-caps section title (e.g. FINTECH & HIGH-TRANSACTION EXPERIENCE)
    summary_lines = []
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if is_header(line, stop_headers):
            break
        # Stop before all-caps subsection titles (keep only prose summary)
        line_clean = line.strip()
        if len(line_clean) > 15 and line_clean.isupper() and " " in line_clean:
            break
        summary_lines.append(line)

    if not summary_lines:
        return ""

    # Merge line wraps into paragraphs: continuation lines get joined with space
    paragraphs = []
    current = []
    for line in summary_lines:
        if not current:
            current.append(line)
            continue
        if _is_continuation_line(line, current[-1]):
            current.append(line)
        else:
            paragraphs.append(" ".join(current))
            current = [line]
    if current:
        paragraphs.append(" ".join(current))

    # Filter out very short or list-only fragments; keep substantial paragraphs
    result = []
    for p in paragraphs:
        p = p.strip()
        if len(p) < 25:
            continue
        # Skip lines that are just " - " bullet fragments
        if p.startswith("- ") and len(p) < 80:
            continue
        result.append(p)

    return "\n\n".join(result) if result else ""


def build_education_from_parser(extracted_data: dict) -> list:
    """Build structured education list from parser's degree and college_name."""
    degree = extracted_data.get("degree") or []
    college = extracted_data.get("college_name")
    if isinstance(degree, str):
        degree = [degree] if degree else []
    result = []
    for d in degree:
        if d and str(d).strip():
            result.append({
                "degree": str(d).strip(),
                "institution": (college or "").strip() if college else "",
                "dates": "",
                "location": "",
            })
    if not result and college and str(college).strip():
        result.append({
            "degree": "",
            "institution": str(college).strip(),
            "dates": "",
            "location": "",
        })
    return result


# Date range pattern: "May 2020 - July 2021" or "December 2019 - May 2020 (6 months)" or "January 2016 - February 2019"
_DATE_RANGE = re.compile(
    r"([A-Za-z]+\s+\d{4})\s*[-–—]\s*([A-Za-z]+\s+\d{4})(?:\s*\([^)]+\))?",
    re.IGNORECASE
)


def parse_experience_entries(flat_experience: list) -> list:
    """Parse flat experience list (parser output) into structured experience_entries."""
    if not flat_experience:
        return []
    lines = [str(x).strip() for x in flat_experience if x and str(x).strip()]
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _DATE_RANGE.search(line):
            # This line is dates; title is typically before, company before that, location after
            dates_str = line
            title = lines[i - 1] if i >= 1 else ""
            company = lines[i - 2] if i >= 2 else ""
            # Skip "Page N of M" and similar
            if title and re.match(r"^Page \d+ of \d+$", title, re.IGNORECASE):
                title = lines[i - 2] if i >= 2 else ""
                company = lines[i - 3] if i >= 3 else ""
            location = lines[i + 1] if i + 1 < len(lines) else ""
            if location and (location.startswith("- ") or _DATE_RANGE.search(location) or len(location) > 80):
                location = ""
            # Collect bullets (lines starting with "- ") until next date or short non-bullet
            bullets = []
            j = i + 2 if location else i + 1
            while j < len(lines):
                next_line = lines[j]
                if _DATE_RANGE.search(next_line):
                    break
                if next_line.startswith("- "):
                    bullets.append(next_line[2:].strip())
                    j += 1
                    continue
                if re.match(r"^Page \d+ of \d+$", next_line, re.IGNORECASE):
                    j += 1
                    continue
                if len(next_line) < 50 and not next_line.startswith("-"):
                    break
                j += 1
            description = bullets
            entries.append({
                "title": title or "",
                "company": company or "",
                "dates": dates_str,
                "location": location or "",
                "description": description,
                "skills": [],
            })
            i = j if j > i + 1 else i + 1
        else:
            i += 1
    return entries


def extract_certifications_from_text(full_text: str) -> list:
    """Extract Certifications section from CV raw text; return list of dicts {name, issuer, issued} or strings."""
    if not full_text or not full_text.strip():
        return []
    text = re.sub(r"\n{3,}", "\n\n", full_text.strip())
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    cert_headers = ("certifications", "certification", "licenses", "licences", "professional certifications")
    stop_headers = ("experience", "work experience", "education", "skills", "projects", "references", "contact", "summary", "page 1 of")

    def is_header(line: str, header_set) -> bool:
        line_lower = line.lower().strip()
        if not line_lower or len(line_lower) > 60:
            return False
        for h in header_set:
            if line_lower == h or line_lower.startswith(h + ":") or line_lower.startswith(h + " "):
                return True
        return False

    start_idx = None
    for i, line in enumerate(lines):
        if is_header(line, cert_headers):
            start_idx = i + 1
            break
    if start_idx is None:
        return []

    result = []
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if is_header(line, stop_headers):
            break
        if len(line) < 5:
            continue
        if re.match(r"^Page \d+ of \d+$", line, re.IGNORECASE):
            continue
        result.append(line)

    out = []
    for line in result:
        line = line.strip()
        if not line:
            continue
        if "–" in line or " - " in line or "," in line:
            parts = re.split(r"\s*[–\-]\s*|\s*,\s*", line, maxsplit=2)
            if len(parts) >= 2:
                name = parts[0].strip()
                rest = " ".join(parts[1:]).strip()
                issued = ""
                if re.search(r"issued\s+\w+\s+\d{4}", rest, re.IGNORECASE):
                    m = re.search(r"(issued\s+\w+\s+\d{4})", rest, re.IGNORECASE)
                    if m:
                        issued = m.group(1)
                        rest = rest.replace(m.group(1), "").strip()
                issuer = rest.strip(" ,")
                out.append({"name": name, "issuer": issuer or "", "issued": issued})
            else:
                out.append({"name": line, "issuer": "", "issued": ""})
        else:
            out.append({"name": line, "issuer": "", "issued": ""})
    return out


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

    # Always build structured data from CV (parser + raw text)
    education = build_education_from_parser(extracted_data)
    if education:
        extracted_data["education"] = education

    experience_entries = parse_experience_entries(extracted_data.get("experience") or [])
    if experience_entries:
        extracted_data["experience_entries"] = experience_entries

    certifications = extract_certifications_from_text(raw_text)
    if certifications:
        extracted_data["certifications"] = certifications

    # Only fill from existing file when the built/extracted value for that key is empty
    if output_path.exists():
        try:
            with open(output_path, encoding="utf-8") as f:
                existing = json.load(f)
            for key in ("experience_entries", "education", "certifications"):
                if not extracted_data.get(key) and key in existing and existing[key]:
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

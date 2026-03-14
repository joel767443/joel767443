#!/usr/bin/env python3
# CV Extractor Script - Saves structured data from any CV PDF to JSON.
# Uses ez-parse (lightweight parser for LinkedIn profile PDFs) plus raw-text
# extraction for experience and education when not provided by ez-parse.
# Extracts: name, email, phone, skills, experience (dates/titles/companies), education, etc.
#
# INSTALL ONCE (run in terminal):
#   pip install -r requirements.txt   # includes ez-parse (and pdfminer)
#
# Works best with LinkedIn "Save to PDF" profiles; still attempts to parse
# experience and education from raw text for other CVs.

import argparse
import io
import json
import re
from pathlib import Path

try:
    from ez_parse import parser as ez_parser
except ImportError:
    # PyPI ez-parse may not install the module; use vendored implementation (same API).
    ez_parser = None

if ez_parser is None:
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage

    _EZ_WEIRD = ["\u00b7", "\xa0", "\uf0da", "\x0c", "• ", "* ", "(LinkedIn)", " (LinkedIn)", "\uf0a7", "(Mobile)", "- ", "●"]

    def _vendored_extract_pdf(fname):
        """Vendored ez-parse: PDF to list of lines."""
        laparams = LAParams()
        retstr = io.StringIO()
        rsrcmgr = PDFResourceManager(caching=True)
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        with open(fname, "rb") as fp:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(fp, caching=True, check_extractable=True):
                interpreter.process_page(page)
        data = retstr.getvalue()
        for i in _EZ_WEIRD:
            data = data.replace(i, "")
        return data.split("\n")

    def _vendored_get_many(result_list):
        """Vendored ez-parse: list of lines to dict (contact, skills, certifications, honors, summary, languages)."""
        TAGS = {"Contact", "Top Skills", "Certifications", "Honors-Awards", "Publications", "Summary", "Languages", "Experience", "Education"}
        contact, skills, certifications, honors, summary, languages = [], [], [], [], [], []

        def collect_until_tag(lines, start, tags):
            out = []
            for j in range(start + 1, len(lines)):
                if not lines[j].strip():
                    continue
                if "Page" in lines[j]:
                    continue
                if lines[j].strip() in tags:
                    return out, j + 1
                out.append(lines[j].strip())
            return out, len(lines)

        i = 0
        while i < len(result_list):
            line = result_list[i]
            if line.strip() == "Contact":
                contact, i = collect_until_tag(result_list, i, TAGS)
            elif line.strip() in ("Top Skills", "Skills"):
                skills, i = collect_until_tag(result_list, i, TAGS)
            elif line.strip() == "Certifications":
                certifications, i = collect_until_tag(result_list, i, TAGS)
            elif line.strip() == "Honors-Awards":
                honors, i = collect_until_tag(result_list, i, TAGS)
            elif line.strip() == "Summary":
                s, i = collect_until_tag(result_list, i, TAGS)
                summary = [" ".join(s).strip()] if s else []
            elif line.strip() == "Languages":
                languages, i = collect_until_tag(result_list, i, TAGS)
            else:
                i += 1
        return {"contact": contact, "skills": skills, "languages": languages, "certifications": certifications, "honors": honors, "summary": summary}

    class _VendoredParser:
        extract_pdf = staticmethod(_vendored_extract_pdf)
        get_many = staticmethod(_vendored_get_many)

    ez_parser = _VendoredParser()

# Regexes for contact parsing from ez-parse "contact" list
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"[\d\s\-+.()]{7,}")


def _parse_contact_from_ez(contact_list: list) -> dict:
    """Map ez-parse contact list to name, email, mobile_number."""
    out = {"name": "", "email": "", "mobile_number": ""}
    if not contact_list:
        return out
    emails = []
    phones = []
    name_candidates = []
    for s in contact_list:
        s = (s or "").strip()
        if not s or "Page " in s:
            continue
        if _EMAIL_RE.search(s):
            emails.append(_EMAIL_RE.search(s).group(0))
            continue
        if _PHONE_RE.fullmatch(s.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")) or (
            len(s) >= 7 and any(c.isdigit() for c in s) and _PHONE_RE.search(s)
        ):
            phones.append(s)
            continue
        name_candidates.append(s)
    out["email"] = emails[0] if emails else ""
    out["mobile_number"] = phones[0] if phones else ""
    out["name"] = name_candidates[0] if name_candidates else ""
    return out


def _get_section_lines(lines: list, start_headers: tuple, stop_headers: tuple) -> list:
    """Find a section by start headers and collect lines until a stop header."""
    start_idx = None
    for i, line in enumerate(lines):
        line_lower = (line or "").strip().lower()
        if not line_lower:
            continue
        for h in start_headers:
            if line_lower == h.lower() or line_lower.startswith(h.lower() + ":") or line_lower.startswith(h.lower() + " "):
                start_idx = i + 1
                break
        if start_idx is not None:
            break
    if start_idx is None:
        return []
    result = []
    for i in range(start_idx, len(lines)):
        line = (lines[i] or "").strip()
        line_lower = line.lower()
        if re.match(r"^Page \d+ of \d+$", line, re.IGNORECASE):
            continue
        for h in stop_headers:
            if line_lower == h.lower() or line_lower.startswith(h.lower() + ":") or line_lower.startswith(h.lower() + " "):
                return result
        if line:
            result.append(line)
    return result


# Date range pattern for experience/education parsing
_DATE_RANGE = re.compile(
    r"([A-Za-z]+\s+\d{4})\s*[-–—]\s*([A-Za-z]+\s+\d{4})(?:\s*\([^)]+\))?",
    re.IGNORECASE
)


def _extract_experience_section_lines(lines: list) -> list:
    """Extract lines under Experience / Work Experience / Employment for parse_experience_entries."""
    start = ("experience", "work experience", "employment", "professional experience")
    stop = (
        "education", "qualifications", "skills", "certifications", "summary",
        "contact", "references", "honors", "languages", "publications",
        "page 1 of", "page 2 of",
    )
    return _get_section_lines(lines, start, stop)


def _looks_like_institution(s: str) -> bool:
    """True if the line looks like a school/university name."""
    if not s or len(s) > 120:
        return False
    lower = s.lower()
    return any(kw in lower for kw in ("university", "college", "institute", "school", "polytechnic", "academy"))


def _looks_like_degree(s: str) -> bool:
    """True if the line looks like a degree/qualification name."""
    if not s or len(s) > 150:
        return False
    lower = s.lower()
    return any(kw in lower for kw in (
        "degree", "bachelor", "b-tech", "btech", "msc", "m.sc", "ma ", "m.a", "phd", "diploma", "certificate", "qualification",
        "information technology", "computer science", "information systems", "management information",
    ))


def extract_education_from_text(full_text: str) -> list:
    """Extract Education/Qualifications section from CV raw text; return list of {degree, institution, dates, location}."""
    if not full_text or not full_text.strip():
        return []
    text = re.sub(r"\n{3,}", "\n\n", full_text.strip())
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    start = ("education", "qualifications", "academic")
    stop = (
        "experience", "work experience", "skills", "certifications",
        "summary", "contact", "references", "page 1 of",
    )
    section = _get_section_lines(lines, start, stop)
    if not section:
        return []
    # Merge continuation lines, but don't merge when next line starts a new entry (institution, or degree after institution)
    merged = []
    for line in section:
        if re.match(r"^Page \d+ of \d+$", line, re.IGNORECASE):
            continue
        if not merged:
            merged.append(line)
            continue
        if _looks_like_institution(line):
            merged.append(line)
            continue
        if _looks_like_institution(merged[-1]) and _looks_like_degree(line):
            merged.append(line)
            continue
        if _is_continuation_line(line, merged[-1]):
            merged[-1] = (merged[-1] + " " + line).strip()
        else:
            merged.append(line)
    result = []
    i = 0
    while i < len(merged):
        line = merged[i]
        degree = ""
        institution = ""
        dates = ""
        location = ""
        if _DATE_RANGE.search(line):
            dates = line
            i += 1
            result.append({"degree": degree, "institution": institution, "dates": dates, "location": location})
            continue
        first_is_inst = _looks_like_institution(line)
        first_is_deg = _looks_like_degree(line)
        if i + 1 < len(merged):
            second = merged[i + 1]
            second_is_date = bool(_DATE_RANGE.search(second))
            second_is_inst = _looks_like_institution(second)
            second_is_deg = _looks_like_degree(second)
            if second_is_date:
                if first_is_inst and not first_is_deg:
                    institution = line
                else:
                    degree = line
                dates = second
                i += 2
            elif first_is_inst and second_is_deg:
                institution = line
                degree = second
                if i + 2 < len(merged):
                    third = merged[i + 2]
                    if _DATE_RANGE.search(third):
                        dates = third
                        i += 3
                    elif not _looks_like_institution(third) and len(third) < 80:
                        location = third
                        i += 3
                    else:
                        i += 2
                else:
                    i += 2
            elif first_is_deg and second_is_inst:
                degree = line
                institution = second
                if i + 2 < len(merged):
                    third = merged[i + 2]
                    if _DATE_RANGE.search(third):
                        dates = third
                        i += 3
                    elif not _looks_like_institution(third) and len(third) < 80:
                        location = third
                        i += 3
                    else:
                        i += 2
                else:
                    i += 2
            else:
                degree = line
                institution = second
                if i + 2 < len(merged):
                    third = merged[i + 2]
                    if _DATE_RANGE.search(third):
                        dates = third
                        i += 3
                    elif not _looks_like_institution(third) and len(third) < 80:
                        location = third
                        i += 3
                    else:
                        i += 2
                else:
                    i += 2
        else:
            degree = line
            institution = ""
            if _looks_like_institution(line) and _looks_like_degree(line):
                for sep in (") ", ")"):
                    if sep in line:
                        idx = line.rfind(sep)
                        before = line[: idx + 1].strip()
                        after = line[idx + len(sep) :].strip() if sep == ") " else line[idx + 1 :].strip()
                        if before and after and _looks_like_institution(before) and _looks_like_degree(after):
                            institution = before
                            degree = after
                            break
            i += 1
        result.append({"degree": degree, "institution": institution, "dates": dates, "location": location})
    return result


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


def _looks_like_certification(s: str) -> bool:
    """True if the line looks like a certification (and not a section header, job title, or name)."""
    if not s or len(s) < 3:
        return False
    lower = s.lower()
    if lower in ("publications", "honors", "honors-awards", "languages", "experience", "education", "skills", "summary", "contact", "references"):
        return False
    if " | " in s:
        return False
    if re.match(r"^Page \d+ of \d+$", s, re.IGNORECASE):
        return False
    cert_keywords = ("certified", "certificate", "certification", "license", "licence", "ccna", "aws", "cissp", "comptia", "professional", "credential")
    if any(kw in lower for kw in cert_keywords):
        return True
    words = s.split()
    if lower in ("specialist", "action", "the"):
        return False
    if len(words) == 2 and all(len(w) > 0 and w[0].isupper() for w in words) and not any(kw in lower for kw in cert_keywords):
        return False
    return True


def extract_certifications_from_text(full_text: str) -> list:
    """Extract Certifications section from CV raw text; return list of dicts {name, issuer, issued}."""
    if not full_text or not full_text.strip():
        return []
    text = re.sub(r"\n{3,}", "\n\n", full_text.strip())
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    cert_headers = ("certifications", "certification", "licenses", "licences", "professional certifications")
    stop_headers = (
        "experience", "work experience", "education", "skills", "projects", "references",
        "contact", "summary", "page 1 of", "publications", "honors", "honors-awards", "languages",
    )

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

    raw_lines = []
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if is_header(line, stop_headers):
            break
        if len(line) < 5:
            continue
        if re.match(r"^Page \d+ of \d+$", line, re.IGNORECASE):
            continue
        raw_lines.append(line)

    merged = []
    for line in raw_lines:
        if not merged:
            merged.append(line)
            continue
        if _is_continuation_line(line, merged[-1]):
            merged[-1] = (merged[-1] + " " + line).strip()
        else:
            merged.append(line)

    out = []
    for line in merged:
        line = line.strip()
        if not line:
            continue
        if not _looks_like_certification(line):
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
    Uses ez-parse for contact, skills, summary, certifications; raw-text extraction
    for experience and education. Works best with LinkedIn "Save to PDF" profiles.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"CV PDF not found: {pdf_path}")

    if output_json is None:
        _, output_json = get_default_paths()
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Extracting data from: {pdf_path}")
    lines = ez_parser.extract_pdf(str(pdf_path))
    ez_data = ez_parser.get_many(lines)
    raw_text = "\n".join(lines)

    # Build extracted_data from ez-parse output
    contact = _parse_contact_from_ez(ez_data.get("contact") or [])
    extracted_data = {
        "name": contact["name"],
        "email": contact["email"],
        "mobile_number": contact["mobile_number"],
        "skills": list(ez_data.get("skills") or []),
        "summary": "\n\n".join(s for s in (ez_data.get("summary") or []) if s).strip() or "",
        "experience": [],
        "experience_entries": [],
        "education": [],
        "degree": None,
        "college_name": None,
        "certifications": [],
        "designation": None,
        "company_names": None,
        "no_of_pages": None,
        "total_experience": None,
    }
    # Certifications from ez-parse: list of strings -> list of {name, issuer, issued}
    for s in ez_data.get("certifications") or []:
        if (s or "").strip():
            extracted_data["certifications"].append({"name": s.strip(), "issuer": "", "issued": ""})
    # Fallback: use raw-text parser for structured certs (issuer/issued) when ez-parse gave none
    if not extracted_data["certifications"]:
        certs_from_text = extract_certifications_from_text(raw_text)
        if certs_from_text:
            extracted_data["certifications"] = certs_from_text

    # Summary fallback from raw text if ez-parse summary empty
    if not extracted_data["summary"]:
        extracted_data["summary"] = extract_summary_from_text(raw_text)

    # Experience from raw text (ez-parse does not extract Experience/Education)
    flat_experience = _extract_experience_section_lines(lines)
    experience_entries = parse_experience_entries(flat_experience)
    if flat_experience:
        extracted_data["experience"] = flat_experience
    if experience_entries:
        extracted_data["experience_entries"] = experience_entries

    # Education from raw text
    education = extract_education_from_text(raw_text)
    if education:
        extracted_data["education"] = education
        first = education[0]
        extracted_data["degree"] = [first.get("degree")] if first.get("degree") else []
        extracted_data["college_name"] = first.get("institution") or None

    # Fill from existing file when extracted value for that key is empty
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

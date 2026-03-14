# Regenerating the `data/` directory

To fully regenerate the `data/` directory from scratch (e.g. after deleting it), run the scripts in this order:

1. **`python scripts/initial_scan.py`** → produces `projects.json`
2. **`python scripts/tech_stack_detector.py`** → produces `tech_stack.json`
3. **`python scripts/architecture_detector.py`** → produces `architecture.json`
4. **`python scripts/extract_cv.py`** → produces `cv_extracted.json` (with structured education, experience_entries, and certifications derived from the CV)
5. **`python scripts/generate_portfolio.py`** → creates `skill_categories.json` if missing, then `portfolio/README.md` and the skills chart image
6. **`python scripts/generate_site.py`** → creates site

No master script is required; the code is set up so that missing files are created or repopulated when you run the pipeline in this order.

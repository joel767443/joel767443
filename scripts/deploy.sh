# 1. Branch
git checkout -b site

# 2. Remove what you don’t want on the site
rm -f README.md example.env requirements.txt .gitignore
rm -rf templates/ graphs/ data/ scripts/

# 3. Replace with site contents and remove site dir
cp -r site/. .
rm -rf site/

# 4. Ensure .env and portfolio are never committed: minimal .gitignore
echo ".env" > .gitignore
echo "/portfolio" >> .gitignore

# 5. Stage everything, then drop .env from the index if it was ever tracked
git add .
git rm --cached .env 2>/dev/null || true

# 6. Commit and push (fix: use --force with two hyphens)
git commit -m "Update site"
git push site site:main --force

# 7. Back to main and delete local site branch
git checkout main
git branch -D site

git checkout -b readme
rm -f README.md example.env requirements.txt .gitignore
rm -rf templates/ scripts/ site/
cp -r portfolio/README.md .
rm -rf portfolio/
echo ".env" > .gitignore
git add .
git rm --cached .env 2>/dev/null || true
git commit -m "Update readme for GitHub Profile"
git push readme readme:main --force
git checkout main
git branch -D readme
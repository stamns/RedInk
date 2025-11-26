#!/bin/bash

# RedInk Upstream Sync Script
# Helps to sync changes from https://github.com/HisMax/RedInk while preserving Vercel customizations.

UPSTREAM_URL="https://github.com/HisMax/RedInk"
BRANCH="main"

echo "============================================"
echo "RedInk Upstream Sync Tool"
echo "============================================"

# 1. Check if upstream remote exists
if ! git remote | grep -q "upstream"; then
    echo "Adding upstream remote ($UPSTREAM_URL)..."
    git remote add upstream "$UPSTREAM_URL"
fi

# 2. Fetch upstream
echo "Fetching upstream..."
git fetch upstream

# 3. Check for Hi-RedInk branch (Mirror of upstream)
if git show-ref --verify --quiet refs/heads/Hi-RedInk; then
    echo "Updating Hi-RedInk branch..."
    git checkout Hi-RedInk
    git merge upstream/$BRANCH --ff-only || { echo "Hi-RedInk divergence detected. Resetting to upstream/$BRANCH..."; git reset --hard upstream/$BRANCH; }
else
    echo "Creating Hi-RedInk branch tracking upstream/$BRANCH..."
    git checkout -b Hi-RedInk upstream/$BRANCH
fi

# Switch back to previous branch
git checkout -

# 4. Merge upstream into current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Merging upstream/$BRANCH into $CURRENT_BRANCH..."

# Using --no-commit so we can inspect before finishing, 
# but script automation usually implies commit if clean.
# However, given conflicts are likely, we let git stop at conflict.

if git merge upstream/$BRANCH --allow-unrelated-histories; then
    echo "Merge successful!"
else
    echo "============================================"
    echo "CONFLICTS DETECTED"
    echo "============================================"
    echo "Git has stopped the merge due to conflicts."
    echo "Please resolve them manually."
    echo ""
    echo "Refer to CUSTOM_MODIFICATIONS.md for what to preserve."
    echo ""
    echo "Quick Conflict Resolution Strategies:"
    echo "1. frontend/src/* -> Usually accept theirs (upstream)"
    echo "   git checkout --theirs frontend/src/"
    echo ""
    echo "2. backend/app.py -> Check if Vercel logic is compatible. Usually accept theirs."
    echo "   git checkout --theirs backend/app.py"
    echo ""
    echo "3. backend/config.py -> MERGE CAREFULLY. Preserve Env Var logic."
    echo ""
    echo "4. vercel.json / api/index.py -> Keep ours."
    echo "   git checkout --ours vercel.json api/index.py"
    echo ""
    echo "After resolving, run:"
    echo "   git add <files>"
    echo "   git commit"
    exit 1
fi

# 5. Post-merge checks
echo "Verifying critical files..."
if [ ! -f "vercel.json" ]; then
    echo "WARNING: vercel.json missing!"
fi

if [ ! -f "backend/utils/storage.py" ]; then
    echo "WARNING: backend/utils/storage.py missing!"
fi

echo "Sync complete."

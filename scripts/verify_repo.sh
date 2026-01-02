#!/bin/bash
# STCI Repository Verification Script
# Validates repository structure, docs, and schemas

set -e

echo "=== STCI Repository Verification ==="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# 1. Check 000-docs exists and is flat
echo "=== Checking 000-docs/ ==="

if [ -d "000-docs" ]; then
    pass "000-docs/ directory exists"
else
    fail "000-docs/ directory missing"
fi

# Check for subdirectories in 000-docs
SUBDIRS=$(find 000-docs -mindepth 1 -type d 2>/dev/null | wc -l)
if [ "$SUBDIRS" -eq 0 ]; then
    pass "000-docs/ is flat (no subdirectories)"
else
    fail "000-docs/ has subdirectories (violates 6767 v4.2)"
    find 000-docs -mindepth 1 -type d
fi

# 2. Check doc naming follows 6767 pattern
echo ""
echo "=== Checking document naming (6767 standard) ==="

# Pattern: NNN-CC-ABCD-description.ext or 6767-x-CC-ABCD-description.ext
NNN_PATTERN='^[0-9]{3}-[A-Z]{2}-[A-Z]{4}-[a-z0-9-]+\.(md|pdf|txt)$'
CANONICAL_PATTERN='^6767-[a-z]-[A-Z]{2}-[A-Z]{4}-[a-z0-9-]+\.(md|pdf|txt)$'

DOC_COUNT=0
VALID_COUNT=0

for file in 000-docs/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        ((DOC_COUNT++))

        if [[ "$filename" =~ $NNN_PATTERN ]] || [[ "$filename" =~ $CANONICAL_PATTERN ]] || [[ "$filename" == "000-INDEX.md" ]]; then
            ((VALID_COUNT++))
        else
            warn "Non-standard filename: $filename"
        fi
    fi
done

if [ "$DOC_COUNT" -eq "$VALID_COUNT" ]; then
    pass "All $DOC_COUNT docs follow 6767 naming"
else
    echo "  $VALID_COUNT/$DOC_COUNT docs follow 6767 naming"
fi

# 3. Check required docs exist
echo ""
echo "=== Checking required documents ==="

REQUIRED_DOCS=(
    "001-PP-PROD"      # PRD
    "002-AT-ADEC"      # ADR
    "003-DR-STND"      # Observation Schema Spec
    "004-DR-STND"      # Methodology Spec
    "005-DR-SOPS"      # Runbook
)

for prefix in "${REQUIRED_DOCS[@]}"; do
    if ls 000-docs/${prefix}*.md 1>/dev/null 2>&1; then
        pass "Found: ${prefix}-*.md"
    else
        fail "Missing: ${prefix}-*.md"
    fi
done

# 4. Check schemas exist
echo ""
echo "=== Checking schemas ==="

if [ -f "schemas/observation.schema.json" ]; then
    pass "schemas/observation.schema.json exists"
    # Validate JSON
    if python3 -c "import json; json.load(open('schemas/observation.schema.json'))" 2>/dev/null; then
        pass "observation.schema.json is valid JSON"
    else
        fail "observation.schema.json is invalid JSON"
    fi
else
    fail "schemas/observation.schema.json missing"
fi

if [ -f "schemas/stci_daily.schema.json" ]; then
    pass "schemas/stci_daily.schema.json exists"
    # Validate JSON
    if python3 -c "import json; json.load(open('schemas/stci_daily.schema.json'))" 2>/dev/null; then
        pass "stci_daily.schema.json is valid JSON"
    else
        fail "stci_daily.schema.json is invalid JSON"
    fi
else
    fail "schemas/stci_daily.schema.json missing"
fi

# 5. Check fixtures exist
echo ""
echo "=== Checking fixtures ==="

if [ -f "data/fixtures/observations.sample.json" ]; then
    pass "data/fixtures/observations.sample.json exists"
    # Validate JSON
    if python3 -c "import json; json.load(open('data/fixtures/observations.sample.json'))" 2>/dev/null; then
        pass "observations.sample.json is valid JSON"
    else
        fail "observations.sample.json is invalid JSON"
    fi
else
    fail "data/fixtures/observations.sample.json missing"
fi

if [ -f "data/fixtures/methodology.yaml" ]; then
    pass "data/fixtures/methodology.yaml exists"
else
    fail "data/fixtures/methodology.yaml missing"
fi

# 6. Check service structure
echo ""
echo "=== Checking services ==="

SERVICES=("collector" "indexer" "api")
for service in "${SERVICES[@]}"; do
    if [ -d "services/$service" ]; then
        pass "services/$service/ exists"
        if [ -f "services/$service/__init__.py" ]; then
            pass "services/$service/__init__.py exists"
        else
            warn "services/$service/__init__.py missing"
        fi
    else
        fail "services/$service/ missing"
    fi
done

# 7. Check for README
echo ""
echo "=== Checking README ==="

if [ -f "README.md" ]; then
    pass "README.md exists"
    # Check for key sections
    if grep -q "STCI" README.md; then
        pass "README mentions STCI"
    else
        warn "README doesn't mention STCI"
    fi
else
    fail "README.md missing"
fi

# Summary
echo ""
echo "=== Verification Summary ==="
echo ""

if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
else
    echo -e "${RED}$ERRORS errors found${NC}"
fi

if [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}$WARNINGS warnings${NC}"
fi

echo ""
echo "Docs in 000-docs/: $DOC_COUNT"
echo ""

exit $ERRORS

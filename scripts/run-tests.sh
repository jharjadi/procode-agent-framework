#!/bin/bash
# Comprehensive Test Runner Script
# Implements closed-loop testing for hypervelocity development

set -e

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="."
REPORT_DIR="test-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/test_report_${TIMESTAMP}.txt"

# Create report directory
mkdir -p "${REPORT_DIR}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Procode Agent Framework - Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test file
run_test() {
    local test_file=$1
    local test_name=$(basename "$test_file")
    
    echo -e "${YELLOW}Running: ${test_name}${NC}"
    
    if python3 "$test_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED: ${test_name}${NC}"
        echo "✓ PASSED: ${test_name}" >> "${REPORT_FILE}"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}✗ FAILED: ${test_name}${NC}"
        echo "✗ FAILED: ${test_name}" >> "${REPORT_FILE}"
        python3 "$test_file" 2>&1 | tee -a "${REPORT_FILE}"
        ((FAILED_TESTS++))
        return 1
    fi
    ((TOTAL_TESTS++))
}

# Start report
echo "Test Report - ${TIMESTAMP}" > "${REPORT_FILE}"
echo "========================================" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# Find and run all test files
echo -e "${BLUE}Discovering test files...${NC}"
TEST_FILES=$(find . -name "test_*.py" -not -path "./.venv/*" -not -path "./frontend/*" | sort)

if [ -z "$TEST_FILES" ]; then
    echo -e "${YELLOW}No test files found${NC}"
    exit 0
fi

echo -e "${BLUE}Found $(echo "$TEST_FILES" | wc -l) test files${NC}"
echo ""

# Run each test
for test_file in $TEST_FILES; do
    run_test "$test_file"
    ((TOTAL_TESTS++))
    echo ""
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Tests:  ${TOTAL_TESTS}"
echo -e "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed:       ${FAILED_TESTS}${NC}"

# Write summary to report
echo "" >> "${REPORT_FILE}"
echo "========================================" >> "${REPORT_FILE}"
echo "Summary" >> "${REPORT_FILE}"
echo "========================================" >> "${REPORT_FILE}"
echo "Total Tests:  ${TOTAL_TESTS}" >> "${REPORT_FILE}"
echo "Passed:       ${PASSED_TESTS}" >> "${REPORT_FILE}"
echo "Failed:       ${FAILED_TESTS}" >> "${REPORT_FILE}"

# Calculate pass rate
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Pass Rate:    ${PASS_RATE}%"
    echo "Pass Rate:    ${PASS_RATE}%" >> "${REPORT_FILE}"
fi

echo ""
echo -e "${BLUE}Report saved to: ${REPORT_FILE}${NC}"

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi

#!/bin/bash
echo "=========================================="
echo "ReqBot v3.0 Database - Full Test Suite"
echo "=========================================="
echo ""

echo "1. Structure Validation Tests"
echo "------------------------------"
python3 test_database_structure.py 2>&1 | tail -3
echo ""

echo "2. Model Unit Tests (pytest)"
echo "------------------------------"
python3 test_database_models.py 2>&1 | tail -1
echo ""

echo "3. Service Layer Tests (pytest)"
echo "------------------------------"
python3 test_database_services.py 2>&1 | tail -1
echo ""

echo "4. Thread Safety Tests"
echo "------------------------------"
python3 test_thread_safety.py 2>&1 | tail -3
echo ""

echo "=========================================="
echo "Test Suite Complete!"
echo "=========================================="

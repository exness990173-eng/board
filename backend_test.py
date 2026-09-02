#!/usr/bin/env python3
"""
Backend API Test Suite for Exams Made Easy - Full Paper Endpoint
Tests the new /api/full-paper/{paper_id} endpoint for RE-NEET 2026
"""

import requests
import json
import sys
from typing import Dict, List, Any

# Use internal backend URL
BASE_URL = "http://localhost:8001"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str, passed: bool, details: str = ""):
    """Print test result with color coding"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    return passed

def test_full_paper_endpoint():
    """Test 1: GET /api/full-paper/reexam-2026 returns 200 with correct structure"""
    print(f"\n{Colors.BOLD}Test 1: Full Paper Endpoint - Valid Paper ID{Colors.RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/full-paper/reexam-2026", timeout=10)
        
        # Check status code
        if not print_test("Status code is 200", response.status_code == 200, 
                         f"Got: {response.status_code}"):
            return False, None
        
        # Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print_test("Response is valid JSON", False, f"JSON decode error: {e}")
            return False, None
        
        print_test("Response is valid JSON", True)
        
        # Check required fields
        required_fields = ["id", "total_questions", "subjects", "questions"]
        all_present = True
        for field in required_fields:
            present = field in data
            print_test(f"Field '{field}' present", present)
            all_present = all_present and present
        
        if not all_present:
            return False, None
        
        return True, data
        
    except requests.exceptions.RequestException as e:
        print_test("API request successful", False, f"Request error: {e}")
        return False, None

def test_paper_metadata(data: Dict[str, Any]):
    """Test 2: Verify paper metadata (id, total_questions, subjects)"""
    print(f"\n{Colors.BOLD}Test 2: Paper Metadata Validation{Colors.RESET}")
    
    all_passed = True
    
    # Check id
    all_passed &= print_test("Paper ID is 'reexam-2026'", 
                            data.get("id") == "reexam-2026",
                            f"Got: {data.get('id')}")
    
    # Check total_questions
    all_passed &= print_test("Total questions is 180", 
                            data.get("total_questions") == 180,
                            f"Got: {data.get('total_questions')}")
    
    # Check subjects
    expected_subjects = ["Physics", "Chemistry", "Biology"]
    actual_subjects = data.get("subjects", [])
    all_passed &= print_test("Subjects list is correct", 
                            actual_subjects == expected_subjects,
                            f"Expected: {expected_subjects}, Got: {actual_subjects}")
    
    return all_passed

def test_questions_structure(data: Dict[str, Any]):
    """Test 3: Verify questions array structure and fields"""
    print(f"\n{Colors.BOLD}Test 3: Questions Array Structure{Colors.RESET}")
    
    questions = data.get("questions", [])
    all_passed = True
    
    # Check questions count
    all_passed &= print_test("Questions array has 180 items", 
                            len(questions) == 180,
                            f"Got: {len(questions)} questions")
    
    if len(questions) == 0:
        return False
    
    # Check first question structure
    first_q = questions[0]
    required_fields = ["question_no", "subject", "question_image", "solution_image", "answer"]
    
    for field in required_fields:
        present = field in first_q
        all_passed &= print_test(f"Question has '{field}' field", present)
    
    # Sample check: verify a few questions have correct structure
    sample_indices = [0, 50, 100, 179]  # First, middle, and last
    for idx in sample_indices:
        if idx < len(questions):
            q = questions[idx]
            has_all = all(field in q for field in required_fields)
            all_passed &= print_test(f"Question {idx+1} has all required fields", has_all)
    
    return all_passed

def test_subject_distribution(data: Dict[str, Any]):
    """Test 4: Verify subject distribution (45 Physics, 45 Chemistry, 90 Biology)"""
    print(f"\n{Colors.BOLD}Test 4: Subject Distribution{Colors.RESET}")
    
    questions = data.get("questions", [])
    
    # Count by subject
    subject_counts = {"Physics": 0, "Chemistry": 0, "Biology": 0}
    for q in questions:
        subject = q.get("subject")
        if subject in subject_counts:
            subject_counts[subject] += 1
    
    all_passed = True
    
    # Expected distribution
    expected = {"Physics": 45, "Chemistry": 45, "Biology": 90}
    
    for subject, expected_count in expected.items():
        actual_count = subject_counts[subject]
        all_passed &= print_test(f"{subject} has {expected_count} questions", 
                                actual_count == expected_count,
                                f"Got: {actual_count}")
    
    return all_passed

def test_bonus_questions(data: Dict[str, Any]):
    """Test 5: Verify exactly 4 questions have answer=null (Q2, 114, 150, 174)"""
    print(f"\n{Colors.BOLD}Test 5: Bonus Questions (answer=null){Colors.RESET}")
    
    questions = data.get("questions", [])
    
    # Find questions with answer=null
    null_answer_questions = []
    for q in questions:
        if q.get("answer") is None:
            null_answer_questions.append(q.get("question_no"))
    
    all_passed = True
    
    # Check count
    all_passed &= print_test("Exactly 4 questions have answer=null", 
                            len(null_answer_questions) == 4,
                            f"Got: {len(null_answer_questions)} questions with null answer")
    
    # Check specific question numbers
    expected_null = [2, 114, 150, 174]
    all_passed &= print_test("Null answer questions are Q2, Q114, Q150, Q174", 
                            null_answer_questions == expected_null,
                            f"Got: {null_answer_questions}")
    
    # Verify other questions have non-null answers
    non_null_count = sum(1 for q in questions if q.get("answer") is not None)
    all_passed &= print_test("Remaining 176 questions have non-null answers", 
                            non_null_count == 176,
                            f"Got: {non_null_count} questions with non-null answer")
    
    # Sample check: verify some answers are valid letters (a/b/c/d)
    sample_answers = [q.get("answer") for q in questions[:10] if q.get("answer") is not None]
    valid_answers = all(ans in ["a", "b", "c", "d"] for ans in sample_answers)
    all_passed &= print_test("Sample answers are valid letters (a/b/c/d)", 
                            valid_answers,
                            f"Sample: {sample_answers[:5]}")
    
    return all_passed

def test_invalid_paper_id():
    """Test 6: GET /api/full-paper/does-not-exist returns 404"""
    print(f"\n{Colors.BOLD}Test 6: Invalid Paper ID (404 Response){Colors.RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/full-paper/does-not-exist", timeout=10)
        
        passed = print_test("Status code is 404 for non-existent paper", 
                           response.status_code == 404,
                           f"Got: {response.status_code}")
        
        return passed
        
    except requests.exceptions.RequestException as e:
        print_test("API request successful", False, f"Request error: {e}")
        return False

def test_image_endpoints():
    """Test 7: Spot-check image endpoints return 200 with image/png content-type"""
    print(f"\n{Colors.BOLD}Test 7: Image Endpoint Spot Checks{Colors.RESET}")
    
    # Images to test
    test_images = [
        "reexam2026_q1_q.png",
        "reexam2026_q1_s.png",
        "reexam2026_q91_q.png",
        "reexam2026_q180_q.png",
        "reexam2026_q180_s.png"
    ]
    
    all_passed = True
    
    for image_name in test_images:
        try:
            response = requests.get(f"{BASE_URL}/api/chapter-image/{image_name}", timeout=10)
            
            status_ok = response.status_code == 200
            content_type = response.headers.get("Content-Type", "")
            is_image = content_type.startswith("image/")
            
            passed = status_ok and is_image
            all_passed &= print_test(f"Image '{image_name}' accessible", 
                                    passed,
                                    f"Status: {response.status_code}, Type: {content_type}")
            
        except requests.exceptions.RequestException as e:
            all_passed &= print_test(f"Image '{image_name}' accessible", False, f"Error: {e}")
    
    return all_passed

def test_existing_endpoints():
    """Test 8: Sanity check - existing endpoints still work"""
    print(f"\n{Colors.BOLD}Test 8: Existing Endpoints Sanity Check{Colors.RESET}")
    
    all_passed = True
    
    # Test /api/quiz/reexam-2026
    try:
        response = requests.get(f"{BASE_URL}/api/quiz/reexam-2026", timeout=10)
        quiz_ok = response.status_code == 200
        
        if quiz_ok:
            quiz_data = response.json()
            question_count = quiz_data.get("count", 0)
            quiz_ok = question_count == 180
            all_passed &= print_test("GET /api/quiz/reexam-2026 returns 200 with 180 questions", 
                                    quiz_ok,
                                    f"Status: {response.status_code}, Questions: {question_count}")
        else:
            all_passed &= print_test("GET /api/quiz/reexam-2026 returns 200", 
                                    False,
                                    f"Status: {response.status_code}")
    except Exception as e:
        all_passed &= print_test("GET /api/quiz/reexam-2026 accessible", False, f"Error: {e}")
    
    # Test /api/subjects
    try:
        response = requests.get(f"{BASE_URL}/api/subjects", timeout=10)
        subjects_ok = response.status_code == 200
        
        if subjects_ok:
            subjects_data = response.json()
            has_subjects = len(subjects_data) > 0
            all_passed &= print_test("GET /api/subjects returns 200 with non-empty list", 
                                    has_subjects,
                                    f"Status: {response.status_code}, Count: {len(subjects_data)}")
        else:
            all_passed &= print_test("GET /api/subjects returns 200", 
                                    False,
                                    f"Status: {response.status_code}")
    except Exception as e:
        all_passed &= print_test("GET /api/subjects accessible", False, f"Error: {e}")
    
    return all_passed

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Backend API Test Suite - Full Paper Endpoint{Colors.RESET}")
    print(f"{Colors.BOLD}Testing: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    
    all_tests_passed = True
    
    # Test 1: Get full paper data
    success, paper_data = test_full_paper_endpoint()
    all_tests_passed &= success
    
    if not success or paper_data is None:
        print(f"\n{Colors.RED}Cannot proceed with further tests - full paper endpoint failed{Colors.RESET}")
        sys.exit(1)
    
    # Test 2: Verify metadata
    all_tests_passed &= test_paper_metadata(paper_data)
    
    # Test 3: Verify questions structure
    all_tests_passed &= test_questions_structure(paper_data)
    
    # Test 4: Verify subject distribution
    all_tests_passed &= test_subject_distribution(paper_data)
    
    # Test 5: Verify bonus questions
    all_tests_passed &= test_bonus_questions(paper_data)
    
    # Test 6: Test invalid paper ID
    all_tests_passed &= test_invalid_paper_id()
    
    # Test 7: Test image endpoints
    all_tests_passed &= test_image_endpoints()
    
    # Test 8: Test existing endpoints
    all_tests_passed &= test_existing_endpoints()
    
    # Final summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    if all_tests_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.RESET}")
        print(f"\n{Colors.GREEN}The Full Paper API endpoint is working correctly!{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}")
        print(f"\n{Colors.RED}Please review the failed tests above.{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

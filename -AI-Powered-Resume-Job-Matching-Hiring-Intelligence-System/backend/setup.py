#!/usr/bin/env python3
"""
Setup and Validation Script for HRTech Platform Backend
Checks dependencies, initializes database, and validates all services
"""

import sys
import subprocess
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error(f"Python 3.9+ required. Current: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if key Python packages are installed"""
    print_header("Checking Python Dependencies")
    
    required_packages = [
        'fastapi',
        'sqlalchemy',
        'spacy',
        'sentence_transformers',
        'PyPDF2',
        'numpy',
        'pandas'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print_error(f"\n{len(missing)} packages missing. Install with:")
        print(f"  pip install -r requirements.txt")
        return False
    return True

def check_database():
    """Check database configuration"""
    print_header("Checking Database Configuration")
    
    try:
        from app.core.config import settings
        print_success(f"Database URL configured")
        print_info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
        return True
    except Exception as e:
        print_error(f"Database configuration error: {e}")
        return False

def initialize_database():
    """Initialize database tables"""
    print_header("Initializing Database Tables")
    
    try:
        from app.core import DatabaseManager
        from app.models import Base
        
        print_info("Creating database tables...")
        DatabaseManager.create_all_tables()
        print_success("Database tables created")
        return True
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        return False

def test_services():
    """Test all backend services"""
    print_header("Testing Backend Services")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Resume Parser
    try:
        from app.services import ResumeParser
        parser = ResumeParser()
        print_success("Resume Parser initialized")
        tests_passed += 1
    except Exception as e:
        print_error(f"Resume Parser: {e}")
        tests_failed += 1
    
    # Test 2: Skill Engine
    try:
        from app.services import SkillExtractor, SkillGraph
        graph = SkillGraph()
        extractor = SkillExtractor(graph)
        
        # Test skill normalization
        normalized = graph.normalize_skill_name("python")
        assert normalized == "Python"
        
        print_success("Skill Engine initialized and working")
        tests_passed += 1
    except Exception as e:
        print_error(f"Skill Engine: {e}")
        tests_failed += 1
    
    # Test 3: Seniority Engine
    try:
        from app.services import SeniorityInference
        engine = SeniorityInference()
        
        # Test inference
        level, conf = engine.infer_from_years_of_experience(5.0)
        assert level.value == "mid_level"
        assert conf > 0
        
        print_success("Seniority Inference Engine working")
        tests_passed += 1
    except Exception as e:
        print_error(f"Seniority Engine: {e}")
        tests_failed += 1
    
    # Test 4: Ranking Model
    try:
        from app.services import RankingModel
        ranker = RankingModel()
        
        # Test skill matching
        score, _, _ = ranker.compute_skill_match_score(
            [{'skill': 'Python'}],
            [{'skill': 'Python'}],
            []
        )
        assert score == 100.0
        
        print_success("Ranking Model initialized and working")
        tests_passed += 1
    except Exception as e:
        print_error(f"Ranking Model: {e}")
        tests_failed += 1
    
    # Test 5: Explainability Engine
    try:
        from app.services.explainability_engine import ExplainabilityEngine
        engine = ExplainabilityEngine()
        
        explanation = engine._generate_skill_explanation(
            ['Python'],
            ['Java'],
            75.0
        )
        assert 'details' in explanation
        
        print_success("Explainability Engine working")
        tests_passed += 1
    except Exception as e:
        print_error(f"Explainability Engine: {e}")
        tests_failed += 1
    
    print_info(f"\nTests passed: {tests_passed}/5")
    return tests_failed == 0

def test_api():
    """Quick API health check"""
    print_header("Testing API Endpoints")
    
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        print_success("Health check endpoint working")
        
        # Test config endpoint
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert 'api_version' in data
        print_success("Config endpoint working")
        
        # Test docs
        response = client.get("/docs")
        assert response.status_code == 200
        print_success("API documentation available")
        
        return True
    except Exception as e:
        print_error(f"API test failed: {e}")
        return False

def main():
    """Main setup and validation"""
    print("\n" + "="*60)
    print("🚀 HRTech Platform Backend - Setup & Validation")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Database Config", check_database),
    ]
    
    # Run initial checks
    for name, check in checks:
        if not check():
            print_error(f"Setup failed at: {name}")
            return False
    
    # Initialize database
    if not initialize_database():
        print_error("Could not initialize database")
        return False
    
    # Test services
    if not test_services():
        print_error("Some services failed initialization")
        return False
    
    # Test API
    if not test_api():
        print_error("API tests failed")
        return False
    
    print_header("✅ Setup Complete!")
    print("""
    Next steps:
    
    1. Start the backend server:
       uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    2. Access the API:
       - OpenAPI Docs: http://localhost:8000/docs
       - ReDoc: http://localhost:8000/redoc
       - Health Check: http://localhost:8000/health
    
    3. Run tests:
       pytest tests/test_backend.py -v
    
    4. See README.md for detailed documentation
    """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Deployment Test Script for ARIA Teaching Assistant
Run this script to verify all components are working correctly.
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    try:
        from scripts.teaching_assistant import StaticsMechanicsTA
        print("✅ Teaching Assistant imported successfully")
    except ImportError as e:
        print(f"❌ Teaching Assistant import failed: {e}")
        return False
    
    try:
        from scripts.embedding.rag_retriever import StaticsMechanicsRAG
        print("✅ RAG Retriever imported successfully")
    except ImportError as e:
        print(f"❌ RAG Retriever import failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test if all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "app.py",
        "requirements.txt",
        "scripts/teaching_assistant.py",
        "scripts/embedding/rag_retriever.py",
        "scripts/database/conversation_storage.py",
        "embeddings/embedding_stats.json",
        "supabase/migrations/001_create_conversations_table.sql",
        ".streamlit/secrets.toml.example",
        "README.md",
        "DEPLOYMENT_GUIDE.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def test_embeddings():
    """Test if embeddings are accessible."""
    print("\n🧠 Testing embeddings...")
    
    try:
        embeddings_path = Path("embeddings")
        if embeddings_path.exists():
            chroma_db = embeddings_path / "chroma_db"
            if chroma_db.exists():
                print("✅ ChromaDB embeddings found")
                return True
            else:
                print("❌ ChromaDB folder not found")
                return False
        else:
            print("❌ Embeddings folder not found")
            return False
    except Exception as e:
        print(f"❌ Error checking embeddings: {e}")
        return False

def test_environment_template():
    """Test if environment template is properly configured."""
    print("\n🔧 Testing environment configuration...")
    
    try:
        secrets_example = Path(".streamlit/secrets.toml.example")
        if secrets_example.exists():
            content = secrets_example.read_text()
            if "OPENAI_API_KEY" in content and "SUPABASE_URL" in content:
                print("✅ Secrets template properly configured")
                return True
            else:
                print("❌ Secrets template missing required variables")
                return False
        else:
            print("❌ Secrets template not found")
            return False
    except Exception as e:
        print(f"❌ Error checking secrets template: {e}")
        return False

def main():
    """Run all deployment tests."""
    print("🚀 ARIA Deployment Test Suite")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_imports),
        ("Embeddings", test_embeddings),
        ("Environment Config", test_environment_template)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Upload to GitHub repository")
        print("2. Deploy on Streamlit Cloud")
        print("3. Configure environment variables")
        print("4. Test live deployment")
    else:
        print("⚠️  Some tests failed. Please fix issues before deployment.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script for pickle-based RAG system
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from scripts.embedding.rag_retriever import StaticsMechanicsRAG

def test_pickle_rag():
    """Test the pickle-based RAG system"""
    print("Testing pickle-based RAG system...")
    
    try:
        # Initialize RAG
        rag = StaticsMechanicsRAG('.')
        
        # Test query
        results = rag.retrieve_relevant_content('What is stress?', n_results=3)
        
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  Source: {result['source']}")
            print(f"  Similarity: {result['similarity_score']:.3f}")
            print(f"  Text preview: {result['text'][:100]}...")
        
        print("\n✅ Pickle-based RAG system working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing RAG system: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pickle_rag()
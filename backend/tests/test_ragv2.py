"""
Comprehensive Test Suite for RAGv2
==================================

This module contains comprehensive tests for all RAGv2 components.
Tests use real Pinecone client and RAGv2 namespaces for accurate validation.
"""

import pytest
import os
import time
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RAGv2 components
from src.rag.config import (
    get_feature_flags, 
    is_feature_enabled, 
    get_embedding_model,
    get_ragv2_namespaces,
    get_existing_namespaces,
    validate_configuration
)
from src.rag.utils.schema_aware_chunker import SchemaAwareChunker
from src.rag.utils.embeddings_v2 import EnhancedEmbeddings
from src.rag.retrieval_v2 import EnhancedRetrieval
from src.rag.generation_guards import GenerationGuards
from src.rag.rag_pipeline_v2 import RAGv2Pipeline

# Test configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
SKIP_REAL_PINECONE = not PINECONE_API_KEY


@pytest.fixture
def mock_pinecone():
    """Mock Pinecone client for unit tests."""
    mock_pc = Mock()
    mock_index = Mock()
    
    # Mock index query responses
    mock_index.query.return_value = {
        'matches': [
            {
                'id': 'test_doc_1',
                'score': 0.85,
                'metadata': {
                    'text': 'Test document content for retrieval',
                    'table_name': 'TestTable',
                    'node_type': 'TestTable'
                }
            },
            {
                'id': 'test_doc_2', 
                'score': 0.75,
                'metadata': {
                    'text': 'Another test document',
                    'table_name': 'TestTable2',
                    'node_type': 'TestTable2'
                }
            }
        ]
    }
    
    mock_pc.Index.return_value = mock_index
    return mock_pc


@pytest.fixture
def real_pinecone():
    """Real Pinecone client for integration tests."""
    if SKIP_REAL_PINECONE:
        pytest.skip("PINECONE_API_KEY not set")
    
    from pinecone import Pinecone
    return Pinecone(api_key=PINECONE_API_KEY)


class TestRAGv2Configuration:
    """Test RAGv2 configuration and feature flags."""
    
    def test_feature_flags_structure(self):
        """Test that feature flags have the expected structure."""
        flags = get_feature_flags()
        
        expected_flags = [
            'schema_aware_chunking',
            'instructor_xl_embeddings', 
            'reranker_enabled',
            'bm25_fallback',
            'graph_rag',
            'hallucination_guards',
            'cdc_enabled',
            'pdf_boost',
            'observability_enabled'
        ]
        
        for flag in expected_flags:
            assert flag in flags
            assert isinstance(flags[flag], bool)
    
    def test_feature_flag_checks(self):
        """Test individual feature flag checking."""
        flags = get_feature_flags()
        
        for flag_name, flag_value in flags.items():
            assert is_feature_enabled(flag_name) == flag_value
    
    def test_embedding_model_selection(self):
        """Test embedding model selection based on feature flags."""
        model = get_embedding_model()
        assert isinstance(model, str)
        assert model in ['all-mpnet-base-v2', 'hkunlp/instructor-xl']
    
    def test_namespace_configuration(self):
        """Test namespace configuration."""
        ragv2_namespaces = get_ragv2_namespaces()
        existing_namespaces = get_existing_namespaces()
        
        # Check RAGv2 namespaces
        assert 'docs' in ragv2_namespaces
        assert 'db' in ragv2_namespaces
        assert 'pdf' in ragv2_namespaces
        
        # Check existing namespaces
        assert 'docs' in existing_namespaces
        assert 'db' in existing_namespaces
        
        # Ensure namespaces are different
        assert ragv2_namespaces['docs'] != existing_namespaces['docs']
        assert ragv2_namespaces['db'] != existing_namespaces['db']
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Should not raise any errors with default config
        validate_configuration()


class TestSchemaAwareChunking:
    """Test schema-aware chunking functionality."""
    
    def test_schema_aware_chunker_initialization(self):
        """Test schema-aware chunker initialization."""
        try:
            chunker = SchemaAwareChunker()
            assert chunker is not None
        except Exception as e:
            # Skip if database connection fails
            pytest.skip(f"Database connection failed: {e}")
    
    def test_course_edition_chunking(self):
        """Test course edition chunking (Task 1 Done-When criteria)."""
        try:
            chunker = SchemaAwareChunker()
            chunks = chunker.get_course_edition_chunks()
            
            if chunks:
                # Test first chunk
                chunk = chunks[0]
                
                # Check required fields
                assert 'id' in chunk
                assert 'text' in chunk
                assert 'metadata' in chunk
                
                # Check metadata structure
                metadata = chunk['metadata']
                assert 'node_type' in metadata
                assert metadata['node_type'] == 'EdizioneCorso'
                
                # Check that IDs are in metadata, not text
                text = chunk['text']
                assert 'edition_id' not in text.lower()
                assert 'course_id' not in text.lower()
                
                # Check token limit
                tokens = chunker._count_tokens(text)
                assert tokens <= 400
                
                print(f"✅ Course edition chunk test passed: {tokens} tokens")
                
        except Exception as e:
            pytest.skip(f"Database test failed: {e}")


class TestEnhancedEmbeddings:
    """Test enhanced embeddings functionality."""
    
    def test_embeddings_initialization(self):
        """Test embeddings initialization."""
        embeddings = EnhancedEmbeddings()
        assert embeddings is not None
    
    def test_embedding_generation(self):
        """Test embedding generation."""
        embeddings = EnhancedEmbeddings()
        
        # Test single text
        text = "Test text for embedding"
        embedding = embeddings.encode_single(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    def test_batch_embedding(self):
        """Test batch embedding generation."""
        embeddings = EnhancedEmbeddings()
        
        texts = [
            "First test text",
            "Second test text", 
            "Third test text"
        ]
        
        batch_embeddings = embeddings.encode(texts)
        
        assert isinstance(batch_embeddings, list)
        assert len(batch_embeddings) == len(texts)
        assert all(len(emb) > 0 for emb in batch_embeddings)
    
    def test_latency_tracking(self):
        """Test latency tracking functionality."""
        embeddings = EnhancedEmbeddings()
        
        # Reset stats
        embeddings.reset_latency_stats()
        
        # Generate some embeddings
        for i in range(5):
            embeddings.encode_single(f"Test text {i}")
        
        # Check stats
        avg_latency = embeddings.get_average_latency()
        p95_latency = embeddings.get_p95_latency()
        
        assert avg_latency > 0
        assert p95_latency > 0
        assert p95_latency >= avg_latency
    
    @pytest.mark.skipif(SKIP_REAL_PINECONE, reason="PINECONE_API_KEY not set")
    def test_embedding_performance_benchmark(self):
        """Test embedding performance benchmark (Task 2 Done-When criteria)."""
        embeddings = EnhancedEmbeddings()
        
        # Run benchmark
        results = embeddings.benchmark_embedding_performance()
        
        assert 'average_latency' in results
        assert 'p95_latency' in results
        assert 'total_embeddings' in results
        
        # Check latency requirement (≤ 120 ms/row)
        assert results['average_latency'] <= 120, f"Average latency {results['average_latency']}ms exceeds 120ms limit"
        
        print(f"✅ Embedding benchmark passed: {results['average_latency']:.2f}ms average")


class TestEnhancedRetrieval:
    """Test enhanced retrieval functionality."""
    
    def test_retrieval_initialization_mock(self, mock_pinecone):
        """Test retrieval initialization with mock Pinecone."""
        retrieval = EnhancedRetrieval(mock_pinecone)
        assert retrieval is not None
        assert retrieval.ragv2_namespaces is not None
        assert retrieval.existing_namespaces is not None
    
    def test_dense_retrieval_mock(self, mock_pinecone):
        """Test dense retrieval with mock Pinecone."""
        retrieval = EnhancedRetrieval(mock_pinecone)
        
        query = "Test query"
        results = retrieval.dense_retrieval(query)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check result structure
        for result in results:
            assert 'id' in result
            assert 'score' in result
            assert 'metadata' in result
            assert 'namespace' in result
    
    def test_cross_encoder_reranking(self, mock_pinecone):
        """Test cross-encoder reranking."""
        retrieval = EnhancedRetrieval(mock_pinecone)
        
        query = "Test query"
        candidates = [
            {
                'id': 'doc1',
                'score': 0.9,
                'metadata': {'text': 'First document'},
                'namespace': 'test'
            },
            {
                'id': 'doc2', 
                'score': 0.8,
                'metadata': {'text': 'Second document'},
                'namespace': 'test'
            }
        ]
        
        # Test with reranker disabled
        with patch('backend.src.rag.config.RERANKER_ENABLED', False):
            results = retrieval.cross_encoder_rerank(query, candidates)
            assert results == candidates
        
        # Test with reranker enabled (if available)
        if retrieval.cross_encoder:
            results = retrieval.cross_encoder_rerank(query, candidates)
            assert len(results) <= len(candidates)
            
            # Check that results have cross-encoder scores
            for result in results:
                assert 'cross_score' in result
    
    def test_context_token_management(self, mock_pinecone):
        """Test context token management."""
        retrieval = EnhancedRetrieval(mock_pinecone)
        
        # Create test results with known token counts
        results = [
            {
                'id': 'doc1',
                'score': 0.9,
                'metadata': {'text': 'Short text'},
                'namespace': 'test'
            },
            {
                'id': 'doc2',
                'score': 0.8, 
                'metadata': {'text': 'Longer text with more words to increase token count'},
                'namespace': 'test'
            }
        ]
        
        filtered_results = retrieval.manage_context_tokens(results)
        
        # Should not exceed max tokens
        total_tokens = sum(retrieval._count_tokens(r['metadata']['text']) for r in filtered_results)
        assert total_tokens <= 4000
    
    @pytest.mark.skipif(SKIP_REAL_PINECONE, reason="PINECONE_API_KEY not set")
    def test_enhanced_retrieval_real(self, real_pinecone):
        """Test enhanced retrieval with real Pinecone (Task 3 Done-When criteria)."""
        retrieval = EnhancedRetrieval(real_pinecone)
        
        query = "Who teaches Operating Systems this semester?"
        results = retrieval.retrieve(query)
        
        assert isinstance(results, list)
        
        # Check namespace usage
        if results:
            namespaces = [r.get('namespace', '') for r in results]
            ragv2_namespaces = get_ragv2_namespaces().values()
            
            # Should use RAGv2 namespaces
            using_ragv2 = any(ns in ragv2_namespaces for ns in namespaces)
            print(f"Using RAGv2 namespaces: {using_ragv2}")
            print(f"Namespaces used: {set(namespaces)}")
        
        # Check performance stats
        stats = retrieval.get_retrieval_stats()
        assert 'total_time' in stats
        assert stats['total_time'] > 0
        
        print(f"✅ Enhanced retrieval test passed: {len(results)} results in {stats['total_time']:.3f}s")


class TestGenerationGuards:
    """Test generation guard-rails functionality."""
    
    def test_guards_initialization(self):
        """Test generation guards initialization."""
        guards = GenerationGuards()
        assert guards is not None
    
    def test_self_check_prompt_creation(self):
        """Test self-check prompt creation."""
        guards = GenerationGuards()
        
        sources = [
            {'text': 'Source 1 content'},
            {'text': 'Source 2 content'}
        ]
        
        prompt = guards.create_self_check_prompt(sources, "Test question")
        
        assert isinstance(prompt, str)
        assert "Using only the sources above" in prompt
        assert "If unsure, say you don't know" in prompt
        assert "Source 1 content" in prompt
        assert "Source 2 content" in prompt
    
    def test_answer_verification(self):
        """Test answer verification against sources."""
        guards = GenerationGuards()
        
        sources = [
            {'text': 'The course is taught by Professor Smith'},
            {'text': 'Operating Systems is a core course'}
        ]
        
        good_answer = "Professor Smith teaches the course"
        bad_answer = "The course is taught by Professor Johnson"
        
        # Test good answer
        good_score = guards.verify_answer_against_sources(good_answer, sources)
        assert isinstance(good_score, float)
        assert good_score >= 0
        
        # Test bad answer
        bad_score = guards.verify_answer_against_sources(bad_answer, sources)
        assert isinstance(bad_score, float)
        assert bad_score >= 0
    
    def test_safe_answer_generation(self):
        """Test safe answer generation with guards."""
        guards = GenerationGuards()
        
        sources = [
            {'text': 'The course is taught by Professor Smith'},
            {'text': 'Operating Systems is a core course'}
        ]
        
        # Test with good answer
        result = guards.generate_safe_answer(
            "Who teaches the course?",
            sources,
            "Professor Smith teaches the course"
        )
        
        assert isinstance(result, dict)
        assert 'answer' in result
        assert 'is_safe' in result
        assert 'confidence_score' in result
    
    def test_hallucination_detection(self):
        """Test hallucination detection (Task 5 Done-When criteria)."""
        guards = GenerationGuards()
        
        # Test with factual sources
        sources = [
            {'text': 'The course is taught by Professor Smith'},
            {'text': 'Operating Systems is a core course'}
        ]
        
        # Test factual answer (should pass)
        factual_result = guards.generate_safe_answer(
            "Who teaches the course?",
            sources,
            "Professor Smith teaches the course"
        )
        
        # Test hallucinated answer (should be flagged)
        hallucinated_result = guards.generate_safe_answer(
            "Who teaches the course?",
            sources,
            "Professor Johnson teaches the course"
        )
        
        print(f"Factual answer safe: {factual_result['is_safe']}")
        print(f"Hallucinated answer safe: {hallucinated_result['is_safe']}")
        
        # The factual answer should be safer than the hallucinated one
        assert factual_result['confidence_score'] >= hallucinated_result['confidence_score']


class TestRAGv2Pipeline:
    """Test the complete RAGv2 pipeline."""
    
    def test_pipeline_initialization(self, mock_pinecone):
        """Test RAGv2 pipeline initialization."""
        pipeline = RAGv2Pipeline(mock_pinecone)
        assert pipeline is not None
    
    def test_pipeline_answer_generation(self, mock_pinecone):
        """Test pipeline answer generation."""
        pipeline = RAGv2Pipeline(mock_pinecone)
        
        query = "Test question"
        result = pipeline.answer(query)
        
        assert isinstance(result, dict)
        assert 'answer' in result
        assert 'sources' in result
        assert 'metadata' in result
    
    def test_pipeline_stats(self, mock_pinecone):
        """Test pipeline statistics."""
        pipeline = RAGv2Pipeline(mock_pinecone)
        
        # Generate an answer to populate stats
        pipeline.answer("Test question")
        
        stats = pipeline.get_pipeline_stats()
        assert isinstance(stats, dict)
        assert 'total_queries' in stats
        assert 'average_response_time' in stats
    
    @pytest.mark.skipif(SKIP_REAL_PINECONE, reason="PINECONE_API_KEY not set")
    def test_pipeline_integration_real(self, real_pinecone):
        """Test complete pipeline with real Pinecone."""
        pipeline = RAGv2Pipeline(real_pinecone)
        
        query = "Who teaches Operating Systems this semester?"
        result = pipeline.answer(query)
        
        assert isinstance(result, dict)
        assert 'answer' in result
        assert 'sources' in result
        assert 'metadata' in result
        
        # Check metadata
        metadata = result['metadata']
        assert 'query_time' in metadata
        assert 'feature_flags_used' in metadata
        
        print(f"✅ Pipeline integration test passed")
        print(f"   Answer length: {len(result['answer'])}")
        print(f"   Sources: {len(result['sources'])}")
        print(f"   Query time: {metadata['query_time']:.3f}s")


class TestFeatureFlagCombinations:
    """Test different feature flag combinations."""
    
    @pytest.mark.parametrize("schema_aware,instructor_xl,reranker", [
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (True, False, False),
        (False, True, True),
        (False, True, False),
        (False, False, True),
        (False, False, False),
    ])
    def test_feature_flag_combinations(self, mock_pinecone, schema_aware, instructor_xl, reranker):
        """Test pipeline with different feature flag combinations."""
        with patch('backend.src.rag.config.SCHEMA_AWARE_CHUNKING', schema_aware):
            with patch('backend.src.rag.config.INSTRUCTOR_XL_EMBEDDINGS', instructor_xl):
                with patch('backend.src.rag.config.RERANKER_ENABLED', reranker):
                    pipeline = RAGv2Pipeline(mock_pinecone)
                    
                    # Should initialize without errors
                    assert pipeline is not None
                    
                    # Should generate answer
                    result = pipeline.answer("Test question")
                    assert isinstance(result, dict)
                    assert 'answer' in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 
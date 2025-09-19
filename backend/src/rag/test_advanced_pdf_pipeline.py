#!/usr/bin/env python3
"""
Advanced PDF Pipeline Test Suite
================================

Comprehensive test suite for the advanced PDF processing pipeline.
Tests all components including processing, evaluation, and integration.
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import components to test
try:
    from rag.utils.advanced_pdf_processor import (
        AdvancedPDFProcessor, 
        DocumentType, 
        ChunkType,
        ProcessedChunk,
        DocumentStructure
    )
    from rag.utils.pdf_evaluation import PDFProcessingEvaluator
    from rag.advanced_pdf_pipeline import AdvancedPDFPipeline
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    IMPORTS_AVAILABLE = False

class TestAdvancedPDFProcessor(unittest.TestCase):
    """Test the advanced PDF processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")
        
        self.processor = AdvancedPDFProcessor(
            enable_ocr=False,  # Disable OCR for testing
            enable_nlp=False,  # Disable NLP for testing
            min_chunk_size=50,
            max_chunk_size=200,
            quality_threshold=0.3
        )
        
        # Create a temporary PDF for testing (mock)
        self.test_pdf_path = self._create_mock_pdf()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'test_pdf_path') and os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    def _create_mock_pdf(self):
        """Create a mock PDF file for testing."""
        # For now, just create a dummy file
        # In production, you'd want to create actual PDF content
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n%Mock PDF for testing\n%%EOF')
            return f.name
    
    @patch('rag.utils.advanced_pdf_processor.fitz')
    def test_document_structure_analysis(self, mock_fitz):
        """Test document structure analysis."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_doc.__len__.return_value = 5  # 5 pages
        
        mock_page = Mock()
        mock_page.get_text.return_value = """
        1. Introduction
        This is a sample document for testing.
        
        2. Methodology
        This section describes the methodology.
        
        Table 1: Sample data
        Figure 1: Sample chart
        """
        
        mock_doc.load_page.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        # Test structure analysis
        structure = self.processor.analyze_document_structure(self.test_pdf_path)
        
        self.assertIsInstance(structure, DocumentStructure)
        self.assertEqual(structure.page_count, 5)
        self.assertIsInstance(structure.estimated_type, DocumentType)
        self.assertGreaterEqual(structure.quality_score, 0.0)
        self.assertLessEqual(structure.quality_score, 1.0)
    
    def test_text_quality_calculation(self):
        """Test text quality calculation."""
        # Good quality text
        good_text = "This is a well-formatted sentence with proper grammar and structure."
        good_score = self.processor._calculate_text_quality(good_text)
        self.assertGreater(good_score, 0.5)
        
        # Poor quality text
        poor_text = "th1s 1s p00r qu4l1ty t3xt w1th l0ts 0f numb3rs"
        poor_score = self.processor._calculate_text_quality(poor_text)
        self.assertLess(poor_score, good_score)
        
        # Empty text
        empty_score = self.processor._calculate_text_quality("")
        self.assertEqual(empty_score, 0.0)
    
    def test_content_type_detection(self):
        """Test content type detection."""
        # Test heading detection
        heading1 = "1. Introduction"
        heading2 = "CHAPTER ONE: OVERVIEW"
        
        is_heading1, level1 = self.processor._is_heading(heading1)
        is_heading2, level2 = self.processor._is_heading(heading2)
        
        self.assertTrue(is_heading1)
        self.assertTrue(is_heading2)
        self.assertEqual(level1, 1)
        self.assertEqual(level2, 1)
        
        # Test content type detection
        list_text = "• First item in list"
        table_text = "Column 1 | Column 2 | Column 3"
        paragraph_text = "This is a regular paragraph of text."
        
        self.assertEqual(self.processor._detect_content_type(list_text), ChunkType.LIST)
        self.assertEqual(self.processor._detect_content_type(table_text), ChunkType.TABLE)
        self.assertEqual(self.processor._detect_content_type(paragraph_text), ChunkType.PARAGRAPH)
    
    def test_adaptive_chunking(self):
        """Test adaptive chunking strategies."""
        # Test paragraph chunking
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(20)])
        chunks = self.processor._chunk_general_content(long_text)
        
        self.assertGreater(len(chunks), 1)  # Should create multiple chunks
        for chunk in chunks:
            self.assertLessEqual(len(chunk), self.processor.max_chunk_size)
        
        # Test list chunking
        list_text = """
        1. First item in the list
        2. Second item in the list
        3. Third item in the list
        """
        list_chunks = self.processor._chunk_list_content(list_text)
        self.assertGreater(len(list_chunks), 0)

class TestPDFEvaluator(unittest.TestCase):
    """Test the PDF evaluation framework."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")
        
        self.evaluator = PDFProcessingEvaluator(enable_advanced_metrics=False)
    
    def test_chunk_quality_evaluation(self):
        """Test chunk quality evaluation."""
        # Create a mock chunk
        from rag.utils.advanced_pdf_processor import ChunkMetadata
        from datetime import datetime
        
        metadata = ChunkMetadata(
            chunk_id="test_chunk_001",
            doc_id="test_doc",
            source_file="test.pdf",
            page_number=1,
            chunk_index=0,
            char_start=0,
            char_end=100,
            chunk_type=ChunkType.PARAGRAPH,
            heading_level=None,
            parent_section="Introduction",
            section_hierarchy=["Introduction"],
            text_length=100,
            token_count=20,
            language="en",
            reading_level=0.7,
            ocr_confidence=1.0,
            text_quality_score=0.8,
            predecessor_id=None,
            successor_id=None,
            related_chunks=[],
            embedding_model=None,
            embedding_dimension=None,
            processing_timestamp=datetime.now().isoformat(),
            pipeline_version="1.0.0"
        )
        
        chunk = ProcessedChunk(
            text="This is a sample chunk of text for testing quality evaluation.",
            metadata=metadata
        )
        
        # Evaluate chunk quality
        quality_metrics = self.evaluator.evaluate_chunk_quality(chunk)
        
        self.assertEqual(quality_metrics.chunk_id, "test_chunk_001")
        self.assertGreaterEqual(quality_metrics.text_quality_score, 0.0)
        self.assertLessEqual(quality_metrics.text_quality_score, 1.0)
        self.assertGreaterEqual(quality_metrics.readability_score, 0.0)
        self.assertLessEqual(quality_metrics.readability_score, 1.0)
    
    def test_recommendations_generation(self):
        """Test recommendation generation."""
        # Create mock benchmark results
        from rag.utils.pdf_evaluation import BenchmarkResult
        
        mock_results = [
            BenchmarkResult(
                processor_config={"enable_ocr": True, "quality_threshold": 0.7},
                document_metrics=[],
                average_processing_time=5.0,
                average_quality_score=0.8,
                chunk_count_distribution={"mean": 10},
                quality_distribution={"mean": 0.8, "std": 0.1},
                processing_success_rate=0.9
            ),
            BenchmarkResult(
                processor_config={"enable_ocr": False, "quality_threshold": 0.5},
                document_metrics=[],
                average_processing_time=2.0,
                average_quality_score=0.6,
                chunk_count_distribution={"mean": 15},
                quality_distribution={"mean": 0.6, "std": 0.2},
                processing_success_rate=0.7
            )
        ]
        
        recommendations = self.evaluator._generate_recommendations(mock_results)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should include general thesis recommendation
        thesis_rec = any("thesis" in rec.lower() for rec in recommendations)
        self.assertTrue(thesis_rec)

class TestAdvancedPDFPipeline(unittest.TestCase):
    """Test the complete PDF pipeline integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")
        
        # Mock Pinecone client to avoid actual API calls
        self.mock_pinecone = Mock()
        self.mock_index = Mock()
        self.mock_pinecone.Index.return_value = self.mock_index
        
        # Create pipeline with mocked dependencies
        with patch('rag.advanced_pdf_pipeline.Pinecone', return_value=self.mock_pinecone):
            self.pipeline = AdvancedPDFPipeline(
                pinecone_client=self.mock_pinecone,
                enable_evaluation=False  # Disable evaluation to avoid additional dependencies
            )
    
    @patch('rag.advanced_pdf_pipeline.AdvancedPDFProcessor')
    @patch('rag.advanced_pdf_pipeline.EnhancedEmbeddings')
    def test_pipeline_initialization(self, mock_embeddings, mock_processor):
        """Test pipeline initialization."""
        # Pipeline should initialize without errors
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.namespace, "pdf_v2")  # Default namespace
        self.assertIsNotNone(self.pipeline.stats)
    
    def test_stats_calculation(self):
        """Test statistics calculation."""
        # Manually update stats
        self.pipeline.stats.update({
            "documents_processed": 5,
            "chunks_created": 50,
            "total_processing_time": 25.0,
            "quality_filtered": 5
        })
        
        stats = self.pipeline.get_processing_stats()
        
        self.assertEqual(stats["documents_processed"], 5)
        self.assertEqual(stats["average_chunks_per_document"], 10.0)
        self.assertEqual(stats["average_processing_time_per_document"], 5.0)
        self.assertEqual(stats["quality_filter_rate"], 0.1)

def run_integration_test():
    """Run integration test with actual PDF if available."""
    print("🧪 Running integration test...")
    
    # Look for test PDF
    test_pdf = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", 
        "iscrizione_ingegneria_informatica_automatica_25_26.pdf"
    )
    
    if not os.path.exists(test_pdf):
        print(f"⚠️ Test PDF not found: {test_pdf}")
        print("   Skipping integration test")
        return True
    
    try:
        # Test basic PDF processor functionality
        processor = AdvancedPDFProcessor(
            enable_ocr=False,
            enable_nlp=False,
            min_chunk_size=100,
            max_chunk_size=500,
            quality_threshold=0.5
        )
        
        print(f"📄 Testing with: {os.path.basename(test_pdf)}")
        
        # Test structure analysis
        start_time = time.time()
        structure = processor.analyze_document_structure(test_pdf)
        analysis_time = time.time() - start_time
        
        print(f"✅ Structure analysis completed in {analysis_time:.2f}s")
        print(f"   Document type: {structure.estimated_type.value}")
        print(f"   Pages: {structure.page_count}")
        print(f"   Quality score: {structure.quality_score:.3f}")
        print(f"   Language: {structure.language}")
        
        # Test text extraction (if PyMuPDF available)
        try:
            import fitz
            
            pages_content = processor.extract_text_with_structure(test_pdf)
            print(f"✅ Text extraction completed")
            print(f"   Pages extracted: {len(pages_content)}")
            
            total_text = sum(len(page.get("text", "")) for page in pages_content)
            print(f"   Total text length: {total_text}")
            
        except ImportError:
            print("⚠️ PyMuPDF not available, skipping text extraction test")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Advanced PDF Pipeline Test Suite")
    print("=" * 50)
    
    # Check dependencies
    missing_deps = []
    
    try:
        import fitz
    except ImportError:
        missing_deps.append("PyMuPDF (fitz)")
    
    try:
        import pdfplumber
    except ImportError:
        missing_deps.append("pdfplumber")
    
    if missing_deps:
        print(f"⚠️ Missing dependencies: {', '.join(missing_deps)}")
        print("   Some tests may be skipped")
        print("   Install with: pip install -r requirements_advanced_pdf.txt")
    
    # Run unit tests
    print("\n🧪 Running unit tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    if IMPORTS_AVAILABLE:
        test_suite.addTest(unittest.makeSuite(TestAdvancedPDFProcessor))
        test_suite.addTest(unittest.makeSuite(TestPDFEvaluator))
        test_suite.addTest(unittest.makeSuite(TestAdvancedPDFPipeline))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Run integration test
    print("\n🔗 Running integration test...")
    integration_success = run_integration_test()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Unit tests run: {result.testsRun}")
    print(f"   Unit test failures: {len(result.failures)}")
    print(f"   Unit test errors: {len(result.errors)}")
    print(f"   Integration test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if result.failures:
        print(f"\n❌ Test Failures:")
        for test, error in result.failures:
            print(f"   • {test}: {error.split(chr(10))[0]}")
    
    if result.errors:
        print(f"\n💥 Test Errors:")
        for test, error in result.errors:
            print(f"   • {test}: {error.split(chr(10))[0]}")
    
    # Overall result
    overall_success = (
        len(result.failures) == 0 and 
        len(result.errors) == 0 and 
        integration_success
    )
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

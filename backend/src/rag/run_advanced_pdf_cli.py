#!/usr/bin/env python3
"""
Advanced PDF Processing CLI
===========================

Command-line interface for the advanced PDF processing pipeline.
Provides easy access to all PDF processing, evaluation, and search capabilities.

For thesis work, this CLI enables comprehensive PDF processing with quality assessment.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.advanced_pdf_pipeline import AdvancedPDFPipeline
from rag.utils.pdf_evaluation import PDFProcessingEvaluator

def print_banner():
    """Print the CLI banner."""
    print("""
🚀 Advanced PDF Processing Pipeline - Thesis-Grade Quality
========================================================
📄 Intelligent Document Structure Analysis
🧠 Hierarchical Chunking with Context Preservation  
📊 Comprehensive Quality Assessment & Evaluation
🔍 Advanced Search and Retrieval Capabilities
⚡ High-Performance Vector Storage Integration

Optimized for: Academic and Technical Documents
""")

def print_help():
    """Print help information."""
    print("""
📋 Available Commands:
--------------------
• process <file/directory> - Process PDF files through the pipeline
• evaluate <file/directory> - Evaluate processing quality across configurations
• search <query> - Search through processed PDF content
• stats - Show pipeline processing statistics
• test - Run comprehensive test on sample documents
• benchmark - Run performance benchmarks
• help - Show this help message
• quit or exit - Exit the program

Example Usage:
--------------
• process /path/to/document.pdf - Process single PDF
• process /path/to/pdfs/ --recursive - Process directory recursively
• evaluate /path/to/pdfs/ --output results/ - Evaluate with detailed report
• search "machine learning algorithms" - Search processed content
• benchmark --configs fast,balanced,quality - Compare configurations

Advanced Options:
-----------------
• --quality-threshold 0.8 - Set minimum quality threshold
• --namespace custom_pdf - Use custom Pinecone namespace
• --batch-size 50 - Set vector upload batch size
• --enable-ocr - Enable OCR for image-based PDFs
• --enable-nlp - Enable advanced NLP processing
• --output results/ - Specify output directory for reports
""")

def progress_callback(current: int, total: int, filename: str, success: bool):
    """Progress callback for batch processing."""
    status = "✅" if success else "❌"
    percent = (current / total) * 100
    print(f"[{percent:5.1f}%] {status} {filename}")

def format_processing_result(result: dict, verbose: bool = False):
    """Format processing result for display."""
    if result["success"]:
        print(f"✅ Processing successful!")
        print(f"   Processing time: {result['processing_time']:.2f}s")
        print(f"   Chunks generated: {result['chunks_generated']}")
        print(f"   Chunks processed: {result['chunks_processed']}")
        print(f"   Chunks uploaded: {result['chunks_uploaded']}")
        print(f"   Average quality: {result['average_quality_score']:.3f}")
        
        if verbose and result.get("document_structure"):
            structure = result["document_structure"]
            print(f"   Document type: {structure['estimated_type']}")
            print(f"   Pages: {structure['page_count']}")
            print(f"   Quality score: {structure['quality_score']:.3f}")
            print(f"   Language: {structure['language']}")
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        if result.get('processing_time'):
            print(f"   Processing time: {result['processing_time']:.2f}s")

def format_evaluation_result(result: dict):
    """Format evaluation result for display."""
    if "error" in result:
        print(f"❌ Evaluation failed: {result['error']}")
        return
    
    summary = result["evaluation_summary"]
    print(f"📊 Evaluation Summary:")
    print(f"   Configurations tested: {summary['configurations_tested']}")
    print(f"   Evaluation timestamp: {summary['evaluation_timestamp']}")
    
    if result.get("best_configuration"):
        best = result["best_configuration"]
        print(f"\n🏆 Best Configuration:")
        print(f"   Quality score: {best['quality_score']:.3f}")
        print(f"   Success rate: {best['success_rate']:.1%}")
        print(f"   Configuration: {best['configuration']}")
    
    print(f"\n💡 Key Recommendations:")
    for i, rec in enumerate(result.get("recommendations", [])[:3], 1):
        print(f"   {i}. {rec}")

def run_process_command(pipeline: AdvancedPDFPipeline, args):
    """Run the process command."""
    input_path = args.input
    
    if not os.path.exists(input_path):
        print(f"❌ Input path not found: {input_path}")
        return
    
    print(f"🚀 Starting PDF processing: {input_path}")
    start_time = time.time()
    
    if os.path.isfile(input_path):
        # Process single file
        print(f"📄 Processing single PDF: {os.path.basename(input_path)}")
        result = pipeline.process_single_pdf(input_path)
        format_processing_result(result, verbose=True)
    else:
        # Process directory
        print(f"📁 Processing PDF directory: {input_path}")
        print(f"   Recursive: {args.recursive}")
        print(f"   Skip existing: {args.skip_existing}")
        
        result = pipeline.process_pdf_directory(
            input_path,
            recursive=args.recursive,
            skip_existing=args.skip_existing,
            progress_callback=progress_callback
        )
        
        if result["success"]:
            print(f"\n✅ Batch processing completed!")
            print(f"   Files found: {result['files_found']}")
            print(f"   Files processed: {result['files_processed']}")
            print(f"   Successful: {result['successful_files']}")
            print(f"   Failed: {result['failed_files']}")
            print(f"   Total chunks: {result['total_chunks_processed']}")
            print(f"   Total time: {result['total_processing_time']:.2f}s")
            print(f"   Average time per file: {result['average_processing_time']:.2f}s")
            
            # Show error summary if any
            if result['failed_files'] > 0:
                print(f"\n⚠️ Failed Files:")
                for file_result in result['detailed_results']:
                    if not file_result['success']:
                        print(f"   • {file_result['file_name']}: {file_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Batch processing failed: {result.get('error', 'Unknown error')}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ Total execution time: {total_time:.2f}s")

def run_evaluate_command(pipeline: AdvancedPDFPipeline, args):
    """Run the evaluate command."""
    input_path = args.input
    
    if not os.path.exists(input_path):
        print(f"❌ Input path not found: {input_path}")
        return
    
    # Find PDF files
    if os.path.isfile(input_path):
        pdf_files = [input_path]
    else:
        pattern = "**/*.pdf" if args.recursive else "*.pdf"
        pdf_files = [str(p) for p in Path(input_path).glob(pattern)]
    
    if not pdf_files:
        print(f"❌ No PDF files found in: {input_path}")
        return
    
    print(f"🧪 Starting evaluation with {len(pdf_files)} PDF files")
    
    # Define configurations to test
    configurations = []
    if args.configs:
        config_names = args.configs.split(',')
        config_map = {
            "fast": {
                "enable_ocr": False,
                "enable_nlp": False,
                "min_chunk_size": 100,
                "max_chunk_size": 500,
                "quality_threshold": 0.5
            },
            "balanced": {
                "enable_ocr": True,
                "enable_nlp": False,
                "min_chunk_size": 150,
                "max_chunk_size": 600,
                "quality_threshold": 0.6
            },
            "quality": {
                "enable_ocr": True,
                "enable_nlp": True,
                "min_chunk_size": 150,
                "max_chunk_size": 800,
                "quality_threshold": 0.7
            },
            "maximum": {
                "enable_ocr": True,
                "enable_nlp": True,
                "min_chunk_size": 200,
                "max_chunk_size": 1000,
                "quality_threshold": 0.8
            }
        }
        
        for name in config_names:
            if name in config_map:
                configurations.append(config_map[name])
            else:
                print(f"⚠️ Unknown configuration: {name}")
    
    # Run evaluation
    start_time = time.time()
    result = pipeline.evaluate_pipeline_quality(pdf_files, configurations)
    evaluation_time = time.time() - start_time
    
    # Display results
    format_evaluation_result(result)
    
    # Save detailed results if output directory specified
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        
        # Save main report
        report_file = os.path.join(args.output, "evaluation_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary_file = os.path.join(args.output, "evaluation_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"PDF Processing Pipeline Evaluation\n")
            f.write(f"==================================\n\n")
            f.write(f"Evaluation completed in {evaluation_time:.2f} seconds\n")
            f.write(f"PDF files evaluated: {len(pdf_files)}\n")
            f.write(f"Configurations tested: {len(result.get('configuration_comparison', []))}\n\n")
            
            if result.get("best_configuration"):
                best = result["best_configuration"]
                f.write(f"Best Configuration:\n")
                f.write(f"  Quality Score: {best['quality_score']:.3f}\n")
                f.write(f"  Success Rate: {best['success_rate']:.1%}\n")
                f.write(f"  Settings: {best['configuration']}\n\n")
            
            f.write(f"Recommendations:\n")
            for i, rec in enumerate(result.get("recommendations", []), 1):
                f.write(f"  {i}. {rec}\n")
        
        print(f"\n📁 Detailed results saved to: {args.output}")
        print(f"   • Full report: {report_file}")
        print(f"   • Summary: {summary_file}")

def run_search_command(pipeline: AdvancedPDFPipeline, args):
    """Run the search command."""
    query = args.query
    if not query:
        query = input("🔍 Enter search query: ").strip()
    
    if not query:
        print("❌ No query provided")
        return
    
    print(f"🔍 Searching for: '{query}'")
    start_time = time.time()
    
    results = pipeline.search_processed_pdfs(
        query, 
        top_k=args.top_k, 
        min_score=args.min_score
    )
    
    search_time = time.time() - start_time
    
    if not results:
        print("🚫 No results found")
        print("💡 Try:")
        print("   • Using different keywords")
        print("   • Lowering the minimum score threshold")
        print("   • Checking if PDFs have been processed")
        return
    
    print(f"✅ Found {len(results)} results in {search_time:.3f}s")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n🔸 Result {i}")
        print(f"   📄 Source: {result['source_file']} (page {result['page_number']})")
        print(f"   📊 Score: {result['score']:.3f} | Quality: {result['quality_score']:.3f}")
        if result['section_hierarchy']:
            # Filter out None values and convert to strings
            hierarchy_parts = [str(part) for part in result['section_hierarchy'] if part is not None]
            if hierarchy_parts:
                print(f"   📂 Section: {' > '.join(hierarchy_parts)}")
        print(f"   📝 Type: {result['chunk_type']}")
        print(f"   💬 Text: {result['text'][:300]}{'...' if len(result['text']) > 300 else ''}")

def run_stats_command(pipeline: AdvancedPDFPipeline):
    """Show pipeline statistics."""
    stats = pipeline.get_processing_stats()
    
    print(f"📊 Pipeline Statistics")
    print("=" * 50)
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Chunks created: {stats['chunks_created']}")
    print(f"Vectors uploaded: {stats['vectors_uploaded']}")
    print(f"Quality filtered: {stats['quality_filtered']}")
    print(f"Processing errors: {stats['processing_errors']}")
    print(f"Total processing time: {stats['total_processing_time']:.2f}s")
    print(f"Average quality score: {stats['average_quality_score']:.3f}")
    
    if stats['documents_processed'] > 0:
        print(f"\nCalculated Metrics:")
        print(f"Average chunks per document: {stats.get('average_chunks_per_document', 0):.1f}")
        print(f"Average processing time per doc: {stats.get('average_processing_time_per_document', 0):.2f}s")
        print(f"Quality filter rate: {stats.get('quality_filter_rate', 0):.1%}")
        print(f"Error rate: {stats.get('error_rate', 0):.1%}")

def run_test_command(pipeline: AdvancedPDFPipeline):
    """Run comprehensive test."""
    print("🧪 Running comprehensive pipeline test...")
    
    # Check if test PDF exists
    test_pdf = os.path.join(os.path.dirname(__file__), "..", "..", "data", "iscrizione_ingegneria_informatica_automatica_25_26.pdf")
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        print("💡 Place a test PDF in backend/data/ directory")
        return
    
    print(f"📄 Testing with: {os.path.basename(test_pdf)}")
    
    # Test processing
    start_time = time.time()
    result = pipeline.process_single_pdf(test_pdf)
    test_time = time.time() - start_time
    
    print(f"\n📊 Test Results:")
    format_processing_result(result, verbose=True)
    
    if result["success"]:
        # Test search
        print(f"\n🔍 Testing search functionality...")
        search_results = pipeline.search_processed_pdfs("corso", top_k=3)
        print(f"   Search results: {len(search_results)}")
        
        if search_results:
            print(f"   Top result score: {search_results[0]['score']:.3f}")
    
    print(f"\n⏱️ Total test time: {test_time:.2f}s")

def run_benchmark_command(pipeline: AdvancedPDFPipeline, args):
    """Run performance benchmark."""
    print("🏁 Running performance benchmark...")
    
    # Find PDF files for benchmarking
    test_dir = args.input or os.path.join(os.path.dirname(__file__), "..", "..", "data")
    pdf_files = [str(p) for p in Path(test_dir).glob("*.pdf")]
    
    if not pdf_files:
        print(f"❌ No PDF files found for benchmarking in: {test_dir}")
        return
    
    print(f"📁 Using {len(pdf_files)} PDF files from: {test_dir}")
    
    # Run evaluation
    result = pipeline.evaluate_pipeline_quality(pdf_files)
    format_evaluation_result(result)

def main():
    """Main CLI function."""
    load_dotenv()
    
    print_banner()
    
    # Check environment
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY environment variable is required")
        sys.exit(1)
    
    # Parse command line arguments for non-interactive mode
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Advanced PDF Processing Pipeline")
        parser.add_argument("command", choices=["process", "evaluate", "search", "stats", "test", "benchmark"])
        parser.add_argument("--input", help="Input PDF file or directory")
        parser.add_argument("--query", help="Search query")
        parser.add_argument("--output", help="Output directory")
        parser.add_argument("--namespace", default="pdf_v2", help="Pinecone namespace")
        parser.add_argument("--quality-threshold", type=float, default=0.7, help="Quality threshold")
        parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
        parser.add_argument("--recursive", action="store_true", help="Process directories recursively")
        parser.add_argument("--skip-existing", action="store_true", help="Skip already processed files")
        parser.add_argument("--top-k", type=int, default=10, help="Number of search results")
        parser.add_argument("--min-score", type=float, default=0.7, help="Minimum similarity score")
        parser.add_argument("--configs", help="Comma-separated list of configurations (fast,balanced,quality,maximum)")
        
        args = parser.parse_args()
        
        # Initialize pipeline
        try:
            pipeline = AdvancedPDFPipeline(
                namespace=args.namespace,
                quality_threshold=args.quality_threshold,
                batch_size=args.batch_size
            )
        except Exception as e:
            print(f"❌ Failed to initialize pipeline: {e}")
            sys.exit(1)
        
        # Execute command
        if args.command == "process":
            if not args.input:
                print("❌ --input required for process command")
                sys.exit(1)
            run_process_command(pipeline, args)
        elif args.command == "evaluate":
            if not args.input:
                print("❌ --input required for evaluate command")
                sys.exit(1)
            run_evaluate_command(pipeline, args)
        elif args.command == "search":
            run_search_command(pipeline, args)
        elif args.command == "stats":
            run_stats_command(pipeline)
        elif args.command == "test":
            run_test_command(pipeline)
        elif args.command == "benchmark":
            run_benchmark_command(pipeline, args)
        
        return
    
    # Interactive mode
    try:
        # Initialize pipeline
        pipeline = AdvancedPDFPipeline(enable_evaluation=True)
        print("✅ Advanced PDF Pipeline initialized successfully")
        
        print_help()
        
        # Main interaction loop
        while True:
            try:
                user_input = input("\n📋 Command: ").strip().lower()
                
                if not user_input:
                    continue
                
                if user_input in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input == 'help':
                    print_help()
                    continue
                
                elif user_input == 'stats':
                    run_stats_command(pipeline)
                    continue
                
                elif user_input == 'test':
                    run_test_command(pipeline)
                    continue
                
                elif user_input.startswith('process '):
                    file_path = user_input[8:].strip()
                    if not file_path:
                        file_path = input("📄 Enter PDF file or directory path: ").strip()
                    
                    if os.path.exists(file_path):
                        # Create simple args object
                        class SimpleArgs:
                            def __init__(self):
                                self.input = file_path
                                self.recursive = True
                                self.skip_existing = True
                        
                        run_process_command(pipeline, SimpleArgs())
                    else:
                        print(f"❌ Path not found: {file_path}")
                
                elif user_input.startswith('search '):
                    query = user_input[7:].strip()
                    if not query:
                        query = input("🔍 Enter search query: ").strip()
                    
                    if query:
                        class SimpleArgs:
                            def __init__(self):
                                self.query = query
                                self.top_k = 10
                                self.min_score = 0.7
                        
                        run_search_command(pipeline, SimpleArgs())
                
                elif user_input.startswith('evaluate '):
                    dir_path = user_input[9:].strip()
                    if not dir_path:
                        dir_path = input("📁 Enter PDF directory path: ").strip()
                    
                    if os.path.exists(dir_path):
                        class SimpleArgs:
                            def __init__(self):
                                self.input = dir_path
                                self.recursive = True
                                self.output = None
                                self.configs = "fast,balanced,quality"
                        
                        run_evaluate_command(pipeline, SimpleArgs())
                    else:
                        print(f"❌ Path not found: {dir_path}")
                
                else:
                    print(f"❌ Unknown command: {user_input}")
                    print("💡 Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Bulk PDF Processing and Pinecone Upsert Script
==============================================

This script processes all PDFs in a directory using the advanced PDF pipeline
and upserts them to Pinecone for your RAG system.

Usage:
    python bulk_pdf_upsert.py /path/to/pdf/directory [options]
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
from rag.config import RAGV2_PDF_NAMESPACE

def print_banner():
    """Print the script banner."""
    print("""
 Bulk PDF Processing & Pinecone Upsert
========================================
 Process entire directories of PDFs
 Advanced chunking with context preservation
 Quality assessment and filtering
 Direct upload to Pinecone vector database
 Optimized for thesis-level document processing
""")

def validate_directory(pdf_directory: str) -> tuple:
    """
    Validate the PDF directory and count files.
    
    Returns:
        tuple: (is_valid, pdf_files_list, total_count)
    """
    if not os.path.exists(pdf_directory):
        return False, [], 0
    
    if not os.path.isdir(pdf_directory):
        return False, [], 0
    
    # Find all PDF files
    pdf_files = []
    for root, dirs, files in os.walk(pdf_directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    return True, pdf_files, len(pdf_files)

def progress_callback(current: int, total: int, filename: str, success: bool):
    """Enhanced progress callback with statistics."""
    status = "✅" if success else "❌"
    percent = (current / total) * 100
    remaining = total - current
    
    print(f"[{percent:5.1f}%] {status} {filename}")
    if current % 5 == 0 or current == total:
        print(f"         Progress: {current}/{total} files | {remaining} remaining")

def estimate_processing_time(pdf_count: int, avg_pages_per_pdf: int = 10) -> str:
    """Estimate total processing time."""
    # Rough estimates based on testing
    seconds_per_page = 0.5  # Conservative estimate
    total_seconds = pdf_count * avg_pages_per_pdf * seconds_per_page
    
    if total_seconds < 60:
        return f"{total_seconds:.0f} seconds"
    elif total_seconds < 3600:
        return f"{total_seconds/60:.1f} minutes"
    else:
        return f"{total_seconds/3600:.1f} hours"

def main():
    """Main processing function."""
    parser = argparse.ArgumentParser(description="Bulk PDF Processing and Pinecone Upsert")
    parser.add_argument("pdf_directory", help="Directory containing PDF files")
    parser.add_argument("--namespace", default=RAGV2_PDF_NAMESPACE, 
                       help=f"Pinecone namespace (default: {RAGV2_PDF_NAMESPACE})")
    parser.add_argument("--quality-threshold", type=float, default=0.7,
                       help="Quality threshold for filtering chunks (default: 0.7)")
    parser.add_argument("--batch-size", type=int, default=100,
                       help="Batch size for Pinecone upserts (default: 100)")
    parser.add_argument("--recursive", action="store_true", default=True,
                       help="Process subdirectories recursively (default: True)")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                       help="Skip files already processed (default: True)")
    parser.add_argument("--enable-ocr", action="store_true", default=True,
                       help="Enable OCR for image-based PDFs (default: True)")
    parser.add_argument("--enable-nlp", action="store_true", default=True,
                       help="Enable NLP for advanced processing (default: True)")
    parser.add_argument("--output-report", 
                       help="Save detailed processing report to file")
    parser.add_argument("--dry-run", action="store_true",
                       help="Analyze files without processing (dry run)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed progress information")
    
    args = parser.parse_args()
    
    load_dotenv()
    print_banner()
    
    # Validate environment
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY environment variable is required")
        print("   Please set it in your .env file")
        sys.exit(1)
    
    # Validate directory
    print(f"📁 Validating directory: {args.pdf_directory}")
    is_valid, pdf_files, pdf_count = validate_directory(args.pdf_directory)
    
    if not is_valid:
        print(f"❌ Invalid directory: {args.pdf_directory}")
        sys.exit(1)
    
    if pdf_count == 0:
        print(f"❌ No PDF files found in: {args.pdf_directory}")
        sys.exit(1)
    
    print(f"✅ Found {pdf_count} PDF files")
    
    # Show file list if verbose or small number of files
    if args.verbose or pdf_count <= 10:
        print(f"\n📄 PDF Files Found:")
        for i, pdf_file in enumerate(pdf_files[:10], 1):
            relative_path = os.path.relpath(pdf_file, args.pdf_directory)
            print(f"   {i:2d}. {relative_path}")
        if pdf_count > 10:
            print(f"   ... and {pdf_count - 10} more files")
    
    # Estimate processing time
    estimated_time = estimate_processing_time(pdf_count)
    print(f"⏱️  Estimated processing time: {estimated_time}")
    
    # Configuration summary
    print(f"\n⚙️  Configuration:")
    print(f"   Namespace: {args.namespace}")
    print(f"   Quality threshold: {args.quality_threshold}")
    print(f"   Batch size: {args.batch_size}")
    print(f"   OCR enabled: {args.enable_ocr}")
    print(f"   NLP enabled: {args.enable_nlp}")
    print(f"   Skip existing: {args.skip_existing}")
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - No files will be processed")
        print(f"   This would process {pdf_count} PDF files")
        print(f"   Estimated chunks: {pdf_count * 15} (rough estimate)")
        print(f"   Estimated processing time: {estimated_time}")
        return
    
    # Confirm processing
    if pdf_count > 5:
        response = input(f"\n❓ Process {pdf_count} PDF files? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Processing cancelled")
            sys.exit(0)
    
    print(f"\n🚀 Starting bulk PDF processing...")
    start_time = time.time()
    
    try:
        # Initialize the advanced PDF pipeline
        print(f"🔧 Initializing Advanced PDF Pipeline...")
        pipeline = AdvancedPDFPipeline(
            namespace=args.namespace,
            quality_threshold=args.quality_threshold,
            batch_size=args.batch_size,
            enable_evaluation=True
        )
        print(f"✅ Pipeline initialized successfully")
        
        # Process the directory
        print(f"\n📁 Processing directory: {args.pdf_directory}")
        print(f"{'='*80}")
        
        processing_result = pipeline.process_pdf_directory(
            args.pdf_directory,
            recursive=args.recursive,
            skip_existing=args.skip_existing,
            progress_callback=progress_callback
        )
        
        total_time = time.time() - start_time
        
        # Display results
        print(f"\n{'='*80}")
        print(f"🎉 BULK PROCESSING COMPLETED!")
        print(f"{'='*80}")
        
        if processing_result["success"]:
            print(f"✅ Processing Summary:")
            print(f"   📁 Directory: {args.pdf_directory}")
            print(f"   📄 Files found: {processing_result['files_found']}")
            print(f"   📊 Files processed: {processing_result['files_processed']}")
            print(f"   ✅ Successful: {processing_result['successful_files']}")
            print(f"   ❌ Failed: {processing_result['failed_files']}")
            print(f"   🧩 Total chunks created: {processing_result['total_chunks_processed']}")
            print(f"   ⏱️  Total processing time: {processing_result['total_processing_time']:.2f}s")
            print(f"   📈 Average time per file: {processing_result['average_processing_time']:.2f}s")
            print(f"   🚀 Processing rate: {processing_result['processing_rate']:.2f} files/second")
            
            # Success rate analysis
            success_rate = processing_result['successful_files'] / processing_result['files_found'] * 100
            print(f"   📊 Success rate: {success_rate:.1f}%")
            
            # Show failed files if any
            if processing_result['failed_files'] > 0:
                print(f"\n⚠️  Failed Files ({processing_result['failed_files']}):")
                failed_files = [
                    result for result in processing_result['detailed_results'] 
                    if not result['success']
                ]
                for i, failed in enumerate(failed_files[:5], 1):
                    print(f"   {i}. {failed['file_name']}: {failed.get('error', 'Unknown error')}")
                if len(failed_files) > 5:
                    print(f"   ... and {len(failed_files) - 5} more failed files")
        
        else:
            print(f"❌ Batch processing failed: {processing_result.get('error', 'Unknown error')}")
        
        # Pipeline statistics
        pipeline_stats = pipeline.get_processing_stats()
        print(f"\n📊 Pipeline Statistics:")
        print(f"   Documents processed: {pipeline_stats['documents_processed']}")
        print(f"   Chunks created: {pipeline_stats['chunks_created']}")
        print(f"   Vectors uploaded: {pipeline_stats['vectors_uploaded']}")
        print(f"   Quality filtered: {pipeline_stats['quality_filtered']}")
        print(f"   Average quality score: {pipeline_stats['average_quality_score']:.3f}")
        
        if pipeline_stats['documents_processed'] > 0:
            print(f"   Average chunks per document: {pipeline_stats.get('average_chunks_per_document', 0):.1f}")
            print(f"   Quality filter rate: {pipeline_stats.get('quality_filter_rate', 0):.1%}")
        
        # Pinecone namespace information
        print(f"\n💾 Vector Database:")
        print(f"   Namespace: {args.namespace}")
        print(f"   Vectors uploaded: {pipeline_stats['vectors_uploaded']}")
        print(f"   Ready for RAG queries: ✅")
        
        # Save detailed report if requested
        if args.output_report:
            report_data = {
                "processing_summary": processing_result,
                "pipeline_stats": pipeline_stats,
                "configuration": {
                    "pdf_directory": args.pdf_directory,
                    "namespace": args.namespace,
                    "quality_threshold": args.quality_threshold,
                    "batch_size": args.batch_size,
                    "enable_ocr": args.enable_ocr,
                    "enable_nlp": args.enable_nlp
                },
                "execution_info": {
                    "total_execution_time": total_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "success": processing_result["success"]
                }
            }
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
            
            with open(args.output_report, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n📁 Detailed report saved to: {args.output_report}")
        
        # Next steps
        print(f"\n🎯 Next Steps:")
        print(f"   • Your PDFs are now processed and stored in Pinecone")
        print(f"   • Use namespace '{args.namespace}' for RAG queries")
        print(f"   • Test with: python run_advanced_pdf_cli.py search 'your query'")
        print(f"   • Integrate with your existing RAG pipeline")
        
        print(f"\n✨ Processing completed successfully in {total_time:.2f} seconds!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Processing interrupted by user")
        print(f"   Partial results may be in Pinecone namespace: {args.namespace}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        print(f"   Check your configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()

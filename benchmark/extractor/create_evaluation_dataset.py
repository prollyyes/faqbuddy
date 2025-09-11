#!/usr/bin/env python3
"""
Complete Pipeline for Creating RAG Evaluation Dataset
=====================================================

This script runs the complete pipeline to extract data from Pinecone
and create a dataset for generating 200 ground truths for RAG evaluation.

Usage:
    python create_evaluation_dataset.py [options]

Features:
- Extracts all data from Pinecone namespaces
- Creates formatted dataset for GPT-5
- Generates comprehensive prompts
- Provides clear next steps
"""

import os
import sys
import argparse
from datetime import datetime

# Add the current directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extract_pinecone_for_evaluation import PineconeDataExtractor
from generate_ground_truths import GroundTruthGenerator


def main():
    """Run the complete evaluation dataset creation pipeline."""
    parser = argparse.ArgumentParser(
        description="Create complete evaluation dataset for RAG pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - extract data and create prompt
  python create_evaluation_dataset.py
  
  # Extract more data per namespace
  python create_evaluation_dataset.py --max-vectors 10000
  
  # Specify custom output directory
  python create_evaluation_dataset.py --output-dir ./my_evaluation_data
  
  # Only extract data, skip prompt generation
  python create_evaluation_dataset.py --extract-only
        """
    )
    
    parser.add_argument("--max-vectors", type=int, default=5000,
                       help="Maximum vectors to extract per namespace (default: 5000)")
    parser.add_argument("--output-dir", type=str, default="./extracted_data",
                       help="Output directory for all files (default: ./extracted_data)")
    parser.add_argument("--num-questions", type=int, default=200,
                       help="Number of ground truth questions to generate (default: 200)")
    parser.add_argument("--extract-only", action="store_true",
                       help="Only extract raw data, skip prompt generation")
    parser.add_argument("--skip-extraction", action="store_true",
                       help="Skip data extraction, use existing dataset")
    parser.add_argument("--dataset-path", type=str,
                       help="Path to existing evaluation dataset (required with --skip-extraction)")
    
    args = parser.parse_args()
    
    print("🚀 RAG Evaluation Dataset Creation Pipeline")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"📊 Max vectors per namespace: {args.max_vectors}")
    print(f"❓ Target questions: {args.num_questions}")
    print()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    extracted_data_path = None
    evaluation_dataset_path = None
    
    # Step 1: Extract data from Pinecone (unless skipped)
    if not args.skip_extraction:
        print("📥 Step 1: Extracting data from Pinecone")
        print("-" * 40)
        
        try:
            extractor = PineconeDataExtractor()
            
            # Extract all data
            extracted_data = extractor.extract_all_data(args.max_vectors)
            
            # Save raw extracted data
            extracted_data_path = os.path.join(args.output_dir, f"pinecone_raw_data_{timestamp}.json")
            extractor.save_extracted_data(extracted_data, extracted_data_path)
            
            # Create evaluation dataset
            evaluation_dataset_path = os.path.join(args.output_dir, f"evaluation_dataset_{timestamp}.json")
            extractor.create_evaluation_dataset(extracted_data, evaluation_dataset_path)
            
            print("✅ Data extraction completed successfully!")
            print()
            
        except Exception as e:
            print(f"❌ Error during data extraction: {e}")
            print("Please check your Pinecone configuration and try again.")
            return 1
    
    else:
        # Use existing dataset
        if not args.dataset_path:
            print("❌ Error: --dataset-path is required when using --skip-extraction")
            return 1
        
        if not os.path.exists(args.dataset_path):
            print(f"❌ Error: Dataset file not found: {args.dataset_path}")
            return 1
        
        evaluation_dataset_path = args.dataset_path
        print(f"✅ Using existing dataset: {evaluation_dataset_path}")
        print()
    
    # Step 2: Generate ground truth prompts (unless extraction only)
    if not args.extract_only:
        print("📝 Step 2: Generating ground truth prompts")
        print("-" * 40)
        
        try:
            generator = GroundTruthGenerator(evaluation_dataset_path)
            
            # Generate prompt
            prompt = generator.generate_prompt(args.num_questions)
            
            # Save prompt
            prompt_path = os.path.join(args.output_dir, f"gpt5_prompt_{timestamp}.md")
            generator.save_prompt(prompt, prompt_path)
            
            # Create template
            template_path = os.path.join(args.output_dir, f"ground_truth_template_{timestamp}.json")
            generator.create_ground_truth_template(template_path)
            
            print("✅ Prompt generation completed successfully!")
            print()
            
        except Exception as e:
            print(f"❌ Error during prompt generation: {e}")
            return 1
    
    # Summary and next steps
    print("🎯 Pipeline Summary")
    print("=" * 50)
    print(f"📁 Output directory: {args.output_dir}")
    
    if extracted_data_path:
        print(f"📊 Raw data: {os.path.basename(extracted_data_path)}")
    
    if evaluation_dataset_path:
        print(f"📄 Evaluation dataset: {os.path.basename(evaluation_dataset_path)}")
    
    if not args.extract_only:
        print(f"📝 GPT-5 prompt: gpt5_prompt_{timestamp}.md")
        print(f"📋 Ground truth template: ground_truth_template_{timestamp}.json")
    
    print()
    print("🚀 Next Steps:")
    print("-" * 20)
    
    if args.extract_only:
        print("1. Review the extracted data")
        print("2. Run this script again without --extract-only to generate prompts")
    else:
        print("1. Review the generated prompt file")
        print("2. Use the prompt with GPT-5 to generate 200 ground truths")
        print("3. The prompt includes:")
        print("   - Complete dataset analysis")
        print("   - Detailed instructions for question generation")
        print("   - Sample questions and expected output format")
        print("   - Quality requirements and distribution guidelines")
        print()
        print("4. Alternative: Use the template file for manual ground truth creation")
    
    print()
    print("📚 Files created:")
    for file in os.listdir(args.output_dir):
        if file.startswith(timestamp[:8]):  # Files from today
            print(f"   - {file}")
    
    print()
    print("✅ Pipeline completed successfully!")
    print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

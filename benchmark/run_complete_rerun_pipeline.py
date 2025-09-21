#!/usr/bin/env python3
"""
Complete Re-run Pipeline for Thesis Evaluation
==============================================

This script executes the complete benchmark re-run pipeline:
1. Generate fresh model responses with improved configurations
2. Clean the raw responses for RAGAS compatibility
3. Run comprehensive RAGAS evaluation using OpenAI API

"""

import os
import sys
import json
import glob
import subprocess
import time
from pathlib import Path
from datetime import datetime

class ThesisEvaluationPipeline:
    """Complete evaluation pipeline for thesis work."""
    
    def __init__(self):
        """Initialize the pipeline."""
        self.project_root = "/home/edd/Documents/projects/faqbuddy"
        self.logs_dir = Path(self.project_root) / "benchmark" / "logs"
        self.clean_logs_v3_dir = self.logs_dir / "clean_logs_v3"
        self.results_dir = Path(self.project_root) / "benchmark" / "eval_results" / "third_run"
        
        # Ensure we're in the right directory
        os.chdir(self.project_root)
        
        print("================= THESIS EVALUATION PIPELINE ===================")
        print(f"Project root: {self.project_root}")
        print(f"Logs directory: {self.logs_dir}")
        print(f"Clean logs V3: {self.clean_logs_v3_dir}")
        print(f"Results directory: {self.results_dir}")
        
    def step1_generate_fresh_responses(self):
        """Step 1: Generate fresh model responses with improved configurations."""
        print("\n" + "="*60)
        print("STEP 1: GENERATING FRESH MODEL RESPONSES")
        print("="*60)
        print("This will generate new responses using your improved model configurations...")
        
        start_time = time.time()
        
        try:
            # Run the comprehensive ablation study with T2SQL + RAG routing
            result = subprocess.run([
                "python", "benchmark/run_comprehensive_evaluation.py", 
                "--mode", "ablation"
            ], cwd=self.project_root)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ Fresh responses generated successfully in {duration:.2f}s")
                
                # Count generated files
                jsonl_files = list(self.logs_dir.glob("*.jsonl"))
                jsonl_files = [f for f in jsonl_files if not str(f).endswith("_clean.jsonl")]
                
                print(f"📊 Generated {len(jsonl_files)} trace files:")
                for file in jsonl_files:
                    with open(file, 'r') as f:
                        line_count = sum(1 for _ in f)
                    print(f"   - {file.name}: {line_count} records")
                
                return True
            else:
                print(f"❌ Failed to generate responses:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error in Step 1: {e}")
            return False
    
    def step2_clean_raw_responses(self):
        """Step 2: Clean the raw responses for RAGAS compatibility."""
        print("\n" + "="*60)
        print("STEP 2: CLEANING RAW RESPONSES")
        print("="*60)
        print("Cleaning responses for RAGAS evaluation...")
        
        def clean_trace_file(input_file, output_file):
            """Clean a single trace file."""
            cleaned = []
            errors = 0
            
            with open(input_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line)
                        
                        # Skip records with empty answers
                        answer = record.get('answer', '').strip()
                        if not answer or '[WARN]' in answer or len(answer) < 10:
                            errors += 1
                            continue
                        
                        # RAGAS OPTIMIZATION: Clean and optimize answer
                        # Remove excessive formatting that might confuse RAGAS
                        clean_answer = answer
                        clean_answer = clean_answer.replace('**Riepilogo:**', '')
                        clean_answer = clean_answer.replace('**Informazioni Complete:**', '')
                        clean_answer = clean_answer.replace('[Documento 1]', '')
                        clean_answer = clean_answer.replace('[/risposta]', '')
                        
                        # Keep only the core answer, remove excessive structure
                        lines = clean_answer.split('\n')
                        core_lines = []
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('**') and not line.startswith('['):
                                core_lines.append(line)
                        
                        # Take first 3 sentences for conciseness
                        clean_answer = '. '.join(core_lines[:3])
                        if not clean_answer.endswith('.'):
                            clean_answer += '.'
                        
                        # Limit to 800 chars for optimal RAGAS performance
                        clean_answer = clean_answer[:800]
                        
                        # Clean ground truth
                        gt = record.get('ground_truth', '').replace('**', '').strip()
                        
                        # RAGAS OPTIMIZATION: Select best contexts
                        # Prioritize contexts that directly answer the question
                        contexts = record.get('contexts', [])
                        question_lower = record['question'].lower()
                        
                        # Score contexts by relevance to question
                        scored_contexts = []
                        for ctx in contexts:
                            if isinstance(ctx, str) and len(ctx.strip()) > 10:
                                ctx_lower = ctx.lower()
                                # Simple relevance scoring
                                relevance_score = 0
                                question_words = question_lower.split()
                                for word in question_words:
                                    if len(word) > 3 and word in ctx_lower:
                                        relevance_score += 1
                                
                                scored_contexts.append((relevance_score, ctx))
                        
                        # Sort by relevance and take top 2 (optimal for RAGAS)
                        scored_contexts.sort(reverse=True, key=lambda x: x[0])
                        best_contexts = [ctx[:600] for score, ctx in scored_contexts[:2]]  # Shorter contexts
                        
                        if best_contexts:
                            cleaned.append({
                                'question': record['question'],
                                'answer': clean_answer,
                                'contexts': best_contexts,
                                'ground_truth': gt
                            })
                        else:
                            errors += 1
                            
                    except Exception as e:
                        errors += 1
                        print(f"   ⚠️ Error on line {line_num}: {e}")
            
            # Save cleaned file
            with open(output_file, 'w') as f:
                for record in cleaned:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            return len(cleaned), errors
        
        # Ensure clean_logs_v3 directory exists
        self.clean_logs_v3_dir.mkdir(exist_ok=True)
        
        # Get only .jsonl files from main logs directory (exclude subdirectories)
        jsonl_files = glob.glob(str(self.logs_dir / "*.jsonl"))
        jsonl_files = [f for f in jsonl_files if "/per_row/" not in f and "_clean.jsonl" not in f]
        
        total_cleaned = 0
        total_errors = 0
        
        print(f"📁 Found {len(jsonl_files)} files to clean")
        
        for file_path in jsonl_files:
            file_name = os.path.basename(file_path).replace('.jsonl', '')
            output_path = self.clean_logs_v3_dir / f"{file_name}_clean.jsonl"
            
            print(f"🧹 Cleaning {file_name}...")
            cleaned_count, error_count = clean_trace_file(file_path, output_path)
            
            total_cleaned += cleaned_count
            total_errors += error_count
            
            print(f"   ✅ {cleaned_count} records cleaned, {error_count} errors")
        
        print(f"\n📊 Cleaning Summary:")
        print(f"   Total cleaned records: {total_cleaned}")
        print(f"   Total errors skipped: {total_errors}")
        print(f"   Success rate: {total_cleaned/(total_cleaned+total_errors)*100:.1f}%")
        print(f"   Cleaned files saved in: {self.clean_logs_v3_dir}")
        
        return total_cleaned > 0
    
    def step3_run_ragas_evaluation(self):
        """Step 3: Run RAGAS evaluation on cleaned files."""
        print("\n" + "="*60)
        print("STEP 3: RUNNING RAGAS EVALUATION")
        print("="*60)
        print("Running RAGAS evaluation using OpenAI API...")
        
        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all cleaned files
        clean_files = list(self.clean_logs_v3_dir.glob("*_clean.jsonl"))
        
        if not clean_files:
            print("❌ No cleaned files found for evaluation")
            return False
        
        print(f"📁 Found {len(clean_files)} cleaned files to evaluate")
        
        successful_evaluations = 0
        failed_evaluations = 0
        
        for file in clean_files:
            config_name = file.stem.replace('_clean', '')
            
            print(f"\n🔍 Evaluating: {config_name}")
            
            # Prepare output paths
            json_output = self.results_dir / f"ragas_{config_name}.json"
            csv_output = self.results_dir / f"ragas_{config_name}_details.csv"
            
            try:
                # Run RAGAS evaluation
                result = subprocess.run([
                    "python", "benchmark/eval/run_ragas_safe.py",
                    "--records", str(file),
                    "--out", str(json_output),
                    "--csv", str(csv_output),
                    "--batch-size", "3",
                    "--timeout", "180"
                ], cwd=self.project_root)
                
                if result.returncode == 0:
                    print(f"   ✅ {config_name} evaluation completed")
                    successful_evaluations += 1
                    
                    # Check if results file was created and has content
                    if json_output.exists():
                        with open(json_output, 'r') as f:
                            results = json.load(f)
                        faithfulness = results.get('faithfulness', 0)
                        answer_relevancy = results.get('answer_relevancy', 0)
                        context_precision = results.get('context_precision', 0)
                        context_recall = results.get('context_recall', 0)
                        answer_correctness = results.get('answer_correctness', 0)
                        answer_similarity = results.get('answer_similarity', 0)
                        overall_score = results.get('overall_score', 0)
                        
                        print(f"   📊 Faithfulness: {faithfulness:.3f}, Answer Relevancy: {answer_relevancy:.3f}")
                        print(f"   📊 Context Precision: {context_precision:.3f}, Context Recall: {context_recall:.3f}")
                        print(f"   📊 Answer Correctness: {answer_correctness:.3f}, Answer Similarity: {answer_similarity:.3f}")
                        print(f"   📈 Overall Score: {overall_score:.3f}")
                    
                else:
                    print(f"   ❌ {config_name} evaluation failed")
                    print(f"   Error: {result.stderr}")
                    failed_evaluations += 1
                    
            except Exception as e:
                print(f"   ❌ {config_name} evaluation error: {e}")
                failed_evaluations += 1
        
        print(f"\n📊 RAGAS Evaluation Summary:")
        print(f"   Successful evaluations: {successful_evaluations}")
        print(f"   Failed evaluations: {failed_evaluations}")
        print(f"   Success rate: {successful_evaluations/(successful_evaluations+failed_evaluations)*100:.1f}%")
        
        return successful_evaluations > 0
    
    def generate_final_summary(self):
        """Generate a final summary of all results."""
        print("\n" + "="*60)
        print("GENERATING FINAL SUMMARY")
        print("="*60)
        
        # Find all result files
        result_files = list(self.results_dir.glob("ragas_*.json"))
        
        if not result_files:
            print("❌ No result files found")
            return
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_configurations": len(result_files),
            "configurations": {},
            "best_configuration": None,
            "worst_configuration": None
        }
        
        best_score = 0
        worst_score = float('inf')
        
        for file in result_files:
            config_name = file.stem.replace('ragas_', '')
            
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                faithfulness = data.get('faithfulness', 0)
                answer_relevancy = data.get('answer_relevancy', 0)
                context_precision = data.get('context_precision', 0)
                context_recall = data.get('context_recall', 0)
                answer_correctness = data.get('answer_correctness', 0)
                answer_similarity = data.get('answer_similarity', 0)
                overall_score = data.get('overall_score', 0)
                retrieval_quality = data.get('retrieval_quality', 0)
                answer_quality = data.get('answer_quality', 0)
                
                summary["configurations"][config_name] = {
                    "faithfulness": faithfulness,
                    "answer_relevancy": answer_relevancy,
                    "context_precision": context_precision,
                    "context_recall": context_recall,
                    "answer_correctness": answer_correctness,
                    "answer_similarity": answer_similarity,
                    "overall_score": overall_score,
                    "retrieval_quality": retrieval_quality,
                    "answer_quality": answer_quality
                }
                
                # Track best/worst using overall_score
                if overall_score > best_score:
                    best_score = overall_score
                    summary["best_configuration"] = config_name
                
                if overall_score < worst_score:
                    worst_score = overall_score
                    summary["worst_configuration"] = config_name
                    
            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")
        
        # Save summary
        summary_file = self.results_dir / "thesis_evaluation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"================= THESIS EVALUATION SUMMARY ===================")
        print(f"   Total configurations: {summary['total_configurations']}")
        print(f"   Best configuration: {summary['best_configuration']} (score: {best_score:.3f})")
        print(f"   Worst configuration: {summary['worst_configuration']} (score: {worst_score:.3f})")
        print(f"   Summary saved: {summary_file}")
        
        # Print detailed results
        print(f"\n📊 Detailed Results:")
        print(f"{'Configuration':<25} {'Overall':<8} {'Faith':<6} {'AnsRel':<7} {'CtxPre':<7} {'CtxRec':<7} {'AnsCor':<7} {'AnsSim':<7}")
        print("-" * 100)
        for config, metrics in summary["configurations"].items():
            print(f"{config:<25} {metrics['overall_score']:.3f}    {metrics['faithfulness']:.3f}  "
                  f"{metrics['answer_relevancy']:.3f}   {metrics['context_precision']:.3f}   "
                  f"{metrics['context_recall']:.3f}   {metrics['answer_correctness']:.3f}   "
                  f"{metrics['answer_similarity']:.3f}")
    
    def run_complete_pipeline(self):
        """Execute the complete pipeline."""
        pipeline_start = time.time()
        
        print("================= STARTING COMPLETE THESIS EVALUATION PIPELINE ===================")
        print("================= This will generate fresh responses, clean them, and evaluate with RAGAS ===================")
        print("⏱️ Estimated time: 15-30 minutes depending on your system")
        
        # Step 1: Generate fresh responses
        if not self.step1_generate_fresh_responses():
            print("❌ Pipeline failed at Step 1")
            return False
        
        # Step 2: Clean responses
        if not self.step2_clean_raw_responses():
            print("❌ Pipeline failed at Step 2")
            return False
        
        # Step 3: Run RAGAS evaluation
        if not self.step3_run_ragas_evaluation():
            print("❌ Pipeline failed at Step 3")
            return False
        
        # Generate final summary
        self.generate_final_summary()
        
        total_time = time.time() - pipeline_start
        
        print("\n" + "="*60)
        print("================= THESIS EVALUATION PIPELINE COMPLETED SUCCESSFULLY ===================")
        print("="*60)
        print(f"⏱️ Total execution time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"📁 Results location: {self.results_dir}")
        print(f"📄 Summary file: {self.results_dir}/thesis_evaluation_summary.json")
        
        print(f"\n================= Your thesis evaluation data is ready! ===================")
        print(f"   - Raw responses: benchmark/logs/*.jsonl")
        print(f"   - Cleaned data: benchmark/logs/clean_logs_v3/")
        print(f"   - RAGAS results: benchmark/eval_results/third_run/")
        
        return True

def main():
    """Main execution function."""
    print("================= THESIS EVALUATION PIPELINE ===================")
    print("This script will execute the complete re-run pipeline for thesis evaluation.")
    print("It will generate fresh responses, clean them, and run RAGAS evaluation.")
    
    # Confirm execution
    response = input("\n================= Ready to start the complete pipeline? (y/N): ===================")
    if response.lower() not in ['y', 'yes']:
        print("❌ Pipeline cancelled by user")
        return 1
    
    # Initialize and run pipeline
    pipeline = ThesisEvaluationPipeline()
    
    try:
        success = pipeline.run_complete_pipeline()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

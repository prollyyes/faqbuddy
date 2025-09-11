#!/usr/bin/env python3
"""
Ground Truth Generation for RAG Pipeline Evaluation
===================================================

This script creates a prompt template for generating 200 high-quality ground truths
using a large language model like GPT-5. It processes the extracted Pinecone data
and creates a structured prompt for ground truth generation.

Features:
- Processes extracted Pinecone data
- Creates comprehensive prompt for GPT-5
- Generates diverse question types
- Ensures coverage across all domains
- Provides structured output format
"""

import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime
import argparse

class GroundTruthGenerator:
    """
    Generates ground truth data for RAG pipeline evaluation.
    """
    
    def __init__(self, evaluation_dataset_path: str):
        """
        Initialize the ground truth generator.
        
        Args:
            evaluation_dataset_path: Path to the evaluation dataset JSON file
        """
        self.evaluation_dataset_path = evaluation_dataset_path
        self.dataset = self._load_dataset()
        
        print("🚀 Initializing Ground Truth Generator")
        print(f"   📄 Dataset: {evaluation_dataset_path}")
        print(f"   📊 Total documents: {len(self.dataset.get('documents', []))}")
        print(f"   📂 Namespaces: {len(self.dataset.get('dataset_info', {}).get('namespaces', []))}")
    
    def _load_dataset(self) -> Dict[str, Any]:
        """Load the evaluation dataset."""
        try:
            with open(self.evaluation_dataset_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading evaluation dataset: {e}")
    
    def _analyze_dataset_content(self) -> Dict[str, Any]:
        """Analyze the dataset content to understand its structure and topics."""
        documents = self.dataset.get('documents', [])
        
        analysis = {
            "total_documents": len(documents),
            "namespace_distribution": {},
            "content_types": {},
            "key_topics": [],
            "document_lengths": {
                "min": float('inf'),
                "max": 0,
                "avg": 0
            }
        }
        
        total_length = 0
        
        for doc in documents:
            # Namespace distribution
            namespace = doc.get('namespace', 'unknown')
            analysis["namespace_distribution"][namespace] = analysis["namespace_distribution"].get(namespace, 0) + 1
            
            # Content type analysis
            metadata = doc.get('metadata', {})
            content_type = metadata.get('content_type', metadata.get('chunk_type', 'unknown'))
            analysis["content_types"][content_type] = analysis["content_types"].get(content_type, 0) + 1
            
            # Document length analysis
            text_length = len(doc.get('text', ''))
            total_length += text_length
            analysis["document_lengths"]["min"] = min(analysis["document_lengths"]["min"], text_length)
            analysis["document_lengths"]["max"] = max(analysis["document_lengths"]["max"], text_length)
        
        analysis["document_lengths"]["avg"] = total_length / len(documents) if documents else 0
        
        return analysis
    
    def _create_sample_questions(self) -> List[Dict[str, str]]:
        """Create sample questions based on the dataset content."""
        documents = self.dataset.get('documents', [])
        sample_questions = []
        
        # Sample some documents to create example questions
        for i, doc in enumerate(documents[:10]):  # Use first 10 documents as examples
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            if len(text) > 100:  # Only use substantial documents
                # Create example questions based on content
                if 'corso' in text.lower() or 'laurea' in text.lower():
                    sample_questions.append({
                        "question": f"Quali sono i requisiti per il corso di {metadata.get('course_name', 'studio')}?",
                        "type": "factual",
                        "difficulty": "easy"
                    })
                elif 'esame' in text.lower() or 'valutazione' in text.lower():
                    sample_questions.append({
                        "question": f"Come funziona il sistema di valutazione descritto nel documento?",
                        "type": "procedural",
                        "difficulty": "medium"
                    })
                elif 'iscrizione' in text.lower() or 'registrazione' in text.lower():
                    sample_questions.append({
                        "question": f"Quali sono le procedure di iscrizione menzionate?",
                        "type": "procedural",
                        "difficulty": "easy"
                    })
        
        return sample_questions
    
    def generate_prompt(self, num_questions: int = 200) -> str:
        """
        Generate a comprehensive prompt for GPT-5 to create ground truths.
        
        Args:
            num_questions: Number of questions to generate
            
        Returns:
            Formatted prompt string
        """
        analysis = self._analyze_dataset_content()
        sample_questions = self._create_sample_questions()
        
        prompt = f"""# Task: Generate {num_questions} High-Quality Ground Truth Questions for RAG Pipeline Evaluation

## Context
You are tasked with generating {num_questions} question-answer pairs for evaluating a Retrieval-Augmented Generation (RAG) pipeline for a university FAQ system. The system is designed to answer questions about university procedures, courses, and academic information.

## Dataset Analysis
Based on the provided documents, here's what we have:
- **Total Documents**: {analysis['total_documents']}
- **Namespace Distribution**: {analysis['namespace_distribution']}
- **Content Types**: {analysis['content_types']}
- **Document Length Range**: {analysis['document_lengths']['min']}-{analysis['document_lengths']['max']} characters
- **Average Document Length**: {analysis['document_lengths']['avg']:.0f} characters

## Requirements

### Question Types (Distribute evenly across all types):
1. **Factual Questions (25%)**: Direct facts, definitions, specific information
2. **Procedural Questions (25%)**: How-to questions, step-by-step processes
3. **Comparative Questions (25%)**: Comparing different options, programs, or procedures
4. **Analytical Questions (25%)**: Complex questions requiring synthesis of multiple sources

### Difficulty Levels (Distribute evenly):
1. **Easy (33%)**: Simple, direct questions with clear answers
2. **Medium (34%)**: Questions requiring some context or multiple pieces of information
3. **Hard (33%)**: Complex questions requiring deep understanding and synthesis

### Domain Coverage:
- **Academic**: Course information, degree programs, academic requirements
- **Administrative**: Registration, enrollment, university procedures
- **Procedural**: Step-by-step processes, deadlines, requirements

### Language Requirements:
- All questions must be in **Italian**
- Use formal but accessible language appropriate for university students
- Questions should be clear and unambiguous

## Sample Questions (for reference):
"""
        
        for i, q in enumerate(sample_questions[:5], 1):
            prompt += f"{i}. **{q['type'].title()}** ({q['difficulty']}): {q['question']}\n"
        
        prompt += f"""

## Document Content Preview
Here are some sample documents from the dataset:

"""
        
        # Add sample documents
        documents = self.dataset.get('documents', [])
        for i, doc in enumerate(documents[:5]):
            prompt += f"### Document {i+1} (ID: {doc['id']})\n"
            prompt += f"**Namespace**: {doc['namespace']}\n"
            prompt += f"**Metadata**: {json.dumps(doc['metadata'], indent=2)}\n"
            prompt += f"**Content**: {doc['text'][:500]}{'...' if len(doc['text']) > 500 else ''}\n\n"
        
        prompt += f"""
## Output Format
Generate exactly {num_questions} questions in the following JSON format:

```json
[
  {{
    "id": "gt_001",
    "question": "Qual è la procedura per iscriversi al corso di laurea in Ingegneria Informatica?",
    "expected_answer": "Per iscriversi al corso di laurea in Ingegneria Informatica è necessario...",
    "context_documents": ["doc_id_1", "doc_id_2"],
    "question_type": "procedural",
    "difficulty": "medium",
    "domain": "academic",
    "keywords": ["iscrizione", "laurea", "ingegneria informatica"],
    "reasoning": "This question tests the system's ability to retrieve procedural information about enrollment"
  }},
  // ... continue for all {num_questions} questions
]
```

## Guidelines for Each Question:

1. **Question Quality**: Make questions natural and realistic - they should be questions a real university student would ask
2. **Answer Completeness**: Ensure the expected answer can be derived from the provided documents
3. **Context Documents**: Specify which document IDs should be retrieved (choose 1-3 relevant documents)
4. **Keywords**: Include 3-5 keywords that should be important for retrieval
5. **Reasoning**: Briefly explain why this question tests an important aspect of the RAG pipeline

## Distribution Requirements:
- **Question Types**: 50 factual, 50 procedural, 50 comparative, 50 analytical
- **Difficulty**: 67 easy, 67 medium, 66 hard
- **Domains**: Mix academic, administrative, and procedural questions
- **Language**: All questions in Italian

## Quality Assurance:
- Ensure each question has a clear, factual answer in the provided documents
- Avoid questions that require external knowledge not in the dataset
- Make questions diverse to test different aspects of retrieval and generation
- Include edge cases and challenging scenarios

Generate the {num_questions} questions now:
"""
        
        return prompt
    
    def save_prompt(self, prompt: str, output_path: str) -> None:
        """Save the generated prompt to a file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            file_size = len(prompt.encode('utf-8')) / 1024  # KB
            print(f"✅ Prompt saved successfully ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"❌ Error saving prompt: {e}")
            raise
    
    def create_ground_truth_template(self, output_path: str) -> None:
        """Create a template file for manual ground truth creation."""
        template = {
            "ground_truths": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_questions": 200,
                "dataset_source": self.evaluation_dataset_path,
                "status": "template_ready"
            },
            "instructions": {
                "usage": "Fill in the ground_truths array with question-answer pairs",
                "format": "Each entry should have: id, question, expected_answer, context_documents, question_type, difficulty, domain, keywords, reasoning"
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Ground truth template created: {output_path}")
            
        except Exception as e:
            print(f"❌ Error creating template: {e}")
            raise


def main():
    """Main function to generate ground truth prompts."""
    parser = argparse.ArgumentParser(description="Generate ground truth prompts for RAG evaluation")
    parser.add_argument("--dataset", type=str, required=True,
                       help="Path to the evaluation dataset JSON file")
    parser.add_argument("--output-dir", type=str, default="./ground_truths",
                       help="Output directory for generated files (default: ./ground_truths)")
    parser.add_argument("--num-questions", type=int, default=200,
                       help="Number of questions to generate (default: 200)")
    parser.add_argument("--create-template", action="store_true",
                       help="Also create a template file for manual ground truth creation")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize generator
    generator = GroundTruthGenerator(args.dataset)
    
    # Generate prompt
    print(f"\n📝 Generating prompt for {args.num_questions} questions")
    prompt = generator.generate_prompt(args.num_questions)
    
    # Save prompt
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    prompt_path = os.path.join(args.output_dir, f"gpt5_prompt_{timestamp}.md")
    generator.save_prompt(prompt, prompt_path)
    
    if args.create_template:
        # Create template
        template_path = os.path.join(args.output_dir, f"ground_truth_template_{timestamp}.json")
        generator.create_ground_truth_template(template_path)
    
    print(f"\n🎯 Next steps:")
    print(f"   1. Review the generated prompt: {prompt_path}")
    print(f"   2. Use the prompt with GPT-5 to generate {args.num_questions} ground truths")
    print(f"   3. The prompt includes dataset analysis and detailed instructions")
    
    if args.create_template:
        print(f"   4. Use the template for manual ground truth creation: {template_path}")
    
    print(f"\n✅ Ground truth generation setup completed!")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

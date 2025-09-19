#!/usr/bin/env python3
"""
Ground Truth Creator for RAG Evaluation
======================================

This module helps create and manage ground truth data for comprehensive
RAG evaluation. It provides tools to:
- Extract potential ground truth from existing traces
- Create annotation templates
- Validate ground truth data
- Semi-automatically generate ground truth mappings
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import hashlib

@dataclass
class GroundTruthEntry:
    """Single ground truth entry for evaluation."""
    query_id: str
    question: str
    ground_truth_answer: str
    relevant_chunk_ids: List[str]
    relevant_sections: List[str]
    is_table_query: bool
    query_type: str
    confidence: float = 1.0  # Confidence in this ground truth
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query_id": self.query_id,
            "question": self.question,
            "ground_truth_answer": self.ground_truth_answer,
            "relevant_chunk_ids": self.relevant_chunk_ids,
            "relevant_sections": self.relevant_sections,
            "is_table_query": self.is_table_query,
            "query_type": self.query_type,
            "confidence": self.confidence
        }

class GroundTruthCreator:
    """Helper for creating and managing ground truth data."""
    
    def __init__(self):
        """Initialize the ground truth creator."""
        self.entries: Dict[str, GroundTruthEntry] = {}
        
        # Patterns for detecting query types
        self.table_query_patterns = [
            r'\bquali\s+corsi\b',
            r'\belenca\b',
            r'\bmostra\b',
            r'\blista\b',
            r'\btutti\s+i\b',
            r'\bprofessori?\b.*\binsegna',
            r'\bcorsi?\b.*\binsegnati?\b',
            r'\bemail\b',
            r'\bcontatti?\b',
            r'\bmatricola\b',
            r'\banno\b.*\baccademico\b'
        ]
        
        self.document_query_patterns = [
            r'\bcome\b',
            r'\bquando\b',
            r'\bdove\b',
            r'\bperch[eé]\b',
            r'\bquanto\b',
            r'\bprocedura\b',
            r'\bregolamento\b',
            r'\brequisiti?\b',
            r'\bmodalit[aà]\b',
            r'\bscadenze?\b',
            r'\btermini?\b',
            r'\biscrizione\b',
            r'\bamissione\b'
        ]
    
    def extract_from_traces(self, traces_file: str) -> List[GroundTruthEntry]:
        """
        Extract potential ground truth entries from trace files.
        
        Args:
            traces_file: Path to enhanced traces JSONL file
            
        Returns:
            List of ground truth entries
        """
        print(f"🔍 Extracting ground truth from {traces_file}")
        
        traces = self._load_traces(traces_file)
        entries = []
        
        for i, trace in enumerate(traces):
            if "error" in trace:
                continue
                
            # Create basic entry
            entry = self._create_entry_from_trace(trace, i)
            entries.append(entry)
        
        print(f"📊 Extracted {len(entries)} ground truth entries")
        return entries
    
    def create_annotation_template(self, 
                                 traces_file: str,
                                 output_file: str,
                                 include_suggestions: bool = True):
        """
        Create an annotation template for manual ground truth creation.
        
        Args:
            traces_file: Path to traces file
            output_file: Path to save template
            include_suggestions: Whether to include AI suggestions
        """
        print(f"📝 Creating annotation template from {traces_file}")
        
        entries = self.extract_from_traces(traces_file)
        
        # Create annotation template
        template = {
            "instructions": {
                "overview": "Manual annotation template for RAG evaluation ground truth",
                "fields": {
                    "query_id": "Unique identifier for the query",
                    "question": "The original question (DO NOT MODIFY)",
                    "ground_truth_answer": "The correct/expected answer",
                    "relevant_chunk_ids": "List of chunk IDs that should be retrieved (if known)",
                    "relevant_sections": "List of document sections that are relevant",
                    "is_table_query": "true if query requires structured/table data, false otherwise",
                    "query_type": "Classification: factual, procedural, list, comparison, etc.",
                    "confidence": "Confidence in this ground truth (0.0-1.0)"
                },
                "query_types": [
                    "factual",      # Simple fact lookup
                    "procedural",   # How-to questions
                    "list",         # Questions asking for lists
                    "comparison",   # Comparing multiple items
                    "calculation",  # Math/numeric questions
                    "temporal",     # Time-related questions
                    "contact"       # Contact information requests
                ]
            },
            "entries": []
        }
        
        for entry in entries:
            entry_dict = entry.to_dict()
            
            if include_suggestions:
                # Add AI suggestions
                entry_dict["_suggestions"] = {
                    "query_type_suggestion": self._suggest_query_type(entry.question),
                    "is_table_query_suggestion": self._suggest_is_table_query(entry.question),
                    "relevant_sections_suggestion": self._suggest_relevant_sections(entry.question)
                }
            
            template["entries"].append(entry_dict)
        
        # Save template
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Annotation template saved to {output_file}")
        print(f"📋 Contains {len(entries)} entries for annotation")
        print(f"💡 Include AI suggestions: {include_suggestions}")
    
    def validate_ground_truth(self, ground_truth_file: str) -> Dict[str, Any]:
        """
        Validate ground truth data for completeness and consistency.
        
        Args:
            ground_truth_file: Path to ground truth JSON file
            
        Returns:
            Validation report
        """
        print(f"🔍 Validating ground truth: {ground_truth_file}")
        
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "entries" in data:
            entries = data["entries"]
        else:
            entries = data
        
        report = {
            "total_entries": len(entries),
            "valid_entries": 0,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        # Validate each entry
        query_types = defaultdict(int)
        table_queries = 0
        
        for i, entry in enumerate(entries):
            entry_id = entry.get("query_id", f"entry_{i}")
            
            # Check required fields
            required_fields = ["question", "ground_truth_answer", "is_table_query", "query_type"]
            missing_fields = [field for field in required_fields if field not in entry]
            
            if missing_fields:
                report["errors"].append(f"{entry_id}: Missing fields: {missing_fields}")
                continue
            
            # Check data types
            if not isinstance(entry["is_table_query"], bool):
                report["errors"].append(f"{entry_id}: is_table_query must be boolean")
                continue
            
            # Check confidence if present
            if "confidence" in entry:
                conf = entry["confidence"]
                if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                    report["warnings"].append(f"{entry_id}: Invalid confidence value: {conf}")
            
            # Collect statistics
            query_types[entry["query_type"]] += 1
            if entry["is_table_query"]:
                table_queries += 1
            
            report["valid_entries"] += 1
        
        # Generate statistics
        report["statistics"] = {
            "query_type_distribution": dict(query_types),
            "table_queries": table_queries,
            "document_queries": report["valid_entries"] - table_queries,
            "completion_rate": report["valid_entries"] / report["total_entries"]
        }
        
        # Print validation summary
        print(f"📊 Validation Summary:")
        print(f"   Total entries: {report['total_entries']}")
        print(f"   Valid entries: {report['valid_entries']}")
        print(f"   Errors: {len(report['errors'])}")
        print(f"   Warnings: {len(report['warnings'])}")
        print(f"   Completion rate: {report['statistics']['completion_rate']:.1%}")
        
        if report["errors"]:
            print(f"\n❌ Errors found:")
            for error in report["errors"][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(report["errors"]) > 5:
                print(f"   ... and {len(report['errors']) - 5} more")
        
        return report
    
    def merge_ground_truth_files(self, 
                                file_paths: List[str],
                                output_file: str,
                                resolve_conflicts: str = "latest") -> Dict[str, Any]:
        """
        Merge multiple ground truth files into one.
        
        Args:
            file_paths: List of ground truth file paths
            output_file: Path to save merged file
            resolve_conflicts: How to resolve conflicts ("latest", "highest_confidence", "manual")
            
        Returns:
            Merge report
        """
        print(f"🔄 Merging {len(file_paths)} ground truth files...")
        
        all_entries = {}
        conflicts = []
        
        for file_path in file_paths:
            print(f"   📁 Loading {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and "entries" in data:
                entries = data["entries"]
            else:
                entries = data
            
            for entry in entries:
                question = entry["question"]
                
                if question in all_entries:
                    # Conflict detected
                    conflicts.append({
                        "question": question,
                        "existing": all_entries[question],
                        "new": entry,
                        "source": file_path
                    })
                    
                    # Resolve conflict
                    if resolve_conflicts == "latest":
                        all_entries[question] = entry
                    elif resolve_conflicts == "highest_confidence":
                        existing_conf = all_entries[question].get("confidence", 0.5)
                        new_conf = entry.get("confidence", 0.5)
                        if new_conf > existing_conf:
                            all_entries[question] = entry
                else:
                    all_entries[question] = entry
        
        # Save merged file
        merged_entries = list(all_entries.values())
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_entries, f, indent=2, ensure_ascii=False)
        
        report = {
            "input_files": len(file_paths),
            "total_unique_entries": len(merged_entries),
            "conflicts_detected": len(conflicts),
            "resolution_strategy": resolve_conflicts,
            "output_file": output_file
        }
        
        print(f"✅ Merged ground truth saved to {output_file}")
        print(f"📊 Merge summary:")
        print(f"   Input files: {len(file_paths)}")
        print(f"   Unique entries: {len(merged_entries)}")
        print(f"   Conflicts: {len(conflicts)}")
        
        return report
    
    def _load_traces(self, traces_file: str) -> List[Dict[str, Any]]:
        """Load traces from JSONL file."""
        traces = []
        with open(traces_file, 'r', encoding='utf-8') as f:
            for line in f:
                traces.append(json.loads(line))
        return traces
    
    def _create_entry_from_trace(self, trace: Dict[str, Any], index: int) -> GroundTruthEntry:
        """Create a ground truth entry from a trace."""
        question = trace["question"]
        
        # Generate query ID
        query_id = trace.get("query_id", f"q_{index + 1}")
        
        # Extract ground truth answer
        ground_truth = trace.get("ground_truth", "")
        
        # Extract relevant chunk IDs from retrieval results
        relevant_chunk_ids = []
        if "retrieval_results" in trace:
            # Take top chunks that seem relevant
            for result in trace["retrieval_results"][:3]:  # Top 3 as potentially relevant
                chunk_id = result.get("chunk_id", result.get("id", ""))
                if chunk_id:
                    relevant_chunk_ids.append(chunk_id)
        
        # Extract relevant sections
        relevant_sections = []
        if "section_analysis" in trace:
            relevant_sections = trace["section_analysis"].get("unique_sections", [])
        
        # Detect query type and table query
        is_table_query = self._suggest_is_table_query(question)
        query_type = self._suggest_query_type(question)
        
        return GroundTruthEntry(
            query_id=query_id,
            question=question,
            ground_truth_answer=ground_truth,
            relevant_chunk_ids=relevant_chunk_ids,
            relevant_sections=relevant_sections,
            is_table_query=is_table_query,
            query_type=query_type,
            confidence=0.7  # Medium confidence for auto-generated
        )
    
    def _suggest_is_table_query(self, question: str) -> bool:
        """Suggest whether a question is a table query."""
        question_lower = question.lower()
        
        # Check for table query patterns
        for pattern in self.table_query_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    def _suggest_query_type(self, question: str) -> str:
        """Suggest the type of query."""
        question_lower = question.lower()
        
        # Check for different query types
        if re.search(r'\bquali\b|\belenca\b|\bmostra\b|\blista\b|\btutti\b', question_lower):
            return "list"
        
        if re.search(r'\bcome\b', question_lower):
            return "procedural"
        
        if re.search(r'\bquando\b|\bscadenza\b|\bdata\b', question_lower):
            return "temporal"
        
        if re.search(r'\bemail\b|\bcontatto\b|\btelefono\b', question_lower):
            return "contact"
        
        if re.search(r'\bquanto\b|\bcosti?\b|\bcrediti\b', question_lower):
            return "calculation"
        
        if re.search(r'\bdove\b|\bsede\b|\baula\b', question_lower):
            return "location"
        
        return "factual"  # Default
    
    def _suggest_relevant_sections(self, question: str) -> List[str]:
        """Suggest relevant sections based on question content."""
        question_lower = question.lower()
        sections = []
        
        # Map keywords to sections
        section_keywords = {
            "corsi": ["Offerta Formativa", "Corsi"],
            "professori": ["Docenti", "Staff"],
            "iscrizione": ["Ammissione", "Iscrizione"],
            "tasse": ["Tasse", "Contributi", "Pagamenti"],
            "laurea": ["Laurea", "Titolo"],
            "stage": ["Stage", "Tirocinio"],
            "erasmus": ["Erasmus", "Mobilità"],
            "esami": ["Esami", "Verifica"],
            "calendario": ["Calendario", "Date"],
            "orario": ["Orari", "Lezioni"]
        }
        
        for keyword, section_list in section_keywords.items():
            if keyword in question_lower:
                sections.extend(section_list)
        
        return list(set(sections))  # Remove duplicates

def create_basic_ground_truth(testset_file: str, output_file: str):
    """Create basic ground truth from testset file."""
    print(f"🏗️ Creating basic ground truth from {testset_file}")
    
    creator = GroundTruthCreator()
    
    # Load testset
    testset = []
    with open(testset_file, 'r', encoding='utf-8') as f:
        for line in f:
            testset.append(json.loads(line))
    
    # Create ground truth entries
    entries = []
    for i, item in enumerate(testset):
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        
        entry = GroundTruthEntry(
            query_id=f"q_{i+1}",
            question=question,
            ground_truth_answer=ground_truth,
            relevant_chunk_ids=[],  # To be filled
            relevant_sections=creator._suggest_relevant_sections(question),
            is_table_query=creator._suggest_is_table_query(question),
            query_type=creator._suggest_query_type(question),
            confidence=0.8 if ground_truth else 0.3
        )
        
        entries.append(entry.to_dict())
    
    # Save ground truth
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Basic ground truth saved to {output_file}")
    print(f"📊 Created {len(entries)} ground truth entries")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create and manage ground truth for RAG evaluation")
    parser.add_argument("--mode", choices=["extract", "template", "validate", "merge", "basic"],
                       required=True, help="Operation mode")
    parser.add_argument("--input", help="Input file or directory")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--testset", default="benchmark/data/testset.jsonl",
                       help="Path to testset file")
    parser.add_argument("--include-suggestions", action="store_true",
                       help="Include AI suggestions in template")
    parser.add_argument("--files", nargs="+", help="Multiple files for merge operation")
    
    args = parser.parse_args()
    
    creator = GroundTruthCreator()
    
    if args.mode == "basic":
        # Create basic ground truth from testset
        output_file = args.output or "benchmark/data/ground_truth_basic.json"
        create_basic_ground_truth(args.testset, output_file)
        
    elif args.mode == "extract":
        # Extract from traces
        if not args.input:
            print("❌ --input required for extract mode")
            exit(1)
        entries = creator.extract_from_traces(args.input)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in entries], f, indent=2, ensure_ascii=False)
            print(f"💾 Extracted ground truth saved to {args.output}")
    
    elif args.mode == "template":
        # Create annotation template
        if not args.input or not args.output:
            print("❌ --input and --output required for template mode")
            exit(1)
        creator.create_annotation_template(
            args.input, 
            args.output,
            args.include_suggestions
        )
    
    elif args.mode == "validate":
        # Validate ground truth
        if not args.input:
            print("❌ --input required for validate mode")
            exit(1)
        report = creator.validate_ground_truth(args.input)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📊 Validation report saved to {args.output}")
    
    elif args.mode == "merge":
        # Merge ground truth files
        if not args.files or not args.output:
            print("❌ --files and --output required for merge mode")
            exit(1)
        report = creator.merge_ground_truth_files(args.files, args.output)
        
    print("\n✅ Ground truth operation completed!")

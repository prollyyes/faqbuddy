"""
Advanced PDF Processing Pipeline
========================================================

This module implements a state-of-the-art PDF processing pipeline that:
- Handles both structured and unstructured PDFs
- Uses hierarchical chunking with context preservation
- Extracts comprehensive metadata and document structure
- Implements adaptive chunking strategies
- Provides quality metrics and evaluation

this pipeline ensures maximum context preservation
and utility across diverse document types.
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

# Core PDF processing
import fitz  # PyMuPDF
import pdfplumber

# OCR and image processing
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# NLP and text processing
try:
    import spacy
    from transformers import pipeline
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# Document structure analysis
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Document type classification."""
    STRUCTURED = "structured"  # Well-formatted with clear sections
    UNSTRUCTURED = "unstructured"  # Free-form text
    ACADEMIC = "academic"  # Research papers, theses
    TECHNICAL = "technical"  # Manuals, specifications
    FORM = "form"  # Forms with tables
    MIXED = "mixed"  # Combination of types

class ChunkType(Enum):
    """Types of content chunks."""
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TABLE = "table"
    LIST = "list"
    FIGURE_CAPTION = "figure_caption"
    FOOTER = "footer"
    HEADER = "header"
    METADATA = "metadata"

@dataclass
class DocumentStructure:
    """Document structure analysis result."""
    page_count: int
    has_toc: bool
    heading_levels: List[int]
    table_count: int
    figure_count: int
    list_count: int
    footnote_count: int
    language: str
    estimated_type: DocumentType
    quality_score: float  # 0-1 indicating text extraction quality

@dataclass
class ChunkMetadata:
    """Comprehensive metadata for each chunk."""
    # Basic identifiers
    chunk_id: str
    doc_id: str
    source_file: str
    
    # Position information
    page_number: int
    chunk_index: int
    char_start: int
    char_end: int
    
    # Content classification
    chunk_type: ChunkType
    heading_level: Optional[int]
    parent_section: Optional[str]
    section_hierarchy: List[str]
    
    # Content properties
    text_length: int
    token_count: int
    language: str
    reading_level: float
    
    # Quality metrics
    ocr_confidence: Optional[float]
    text_quality_score: float
    
    # Relationships
    predecessor_id: Optional[str]
    successor_id: Optional[str]
    related_chunks: List[str]
    
    # Embeddings metadata
    embedding_model: Optional[str]
    embedding_dimension: Optional[int]
    
    # Processing metadata
    processing_timestamp: str
    pipeline_version: str

@dataclass
class ProcessedChunk:
    """A processed text chunk with full metadata."""
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None

class AdvancedPDFProcessor:
    """
    State-of-the-art PDF processing pipeline.
    
    Features:
    - Adaptive content extraction (text + OCR)
    - Document structure analysis
    - Hierarchical chunking with context preservation
    - Comprehensive metadata extraction
    - Quality assessment and metrics
    """
    
    def __init__(self, 
                 pipeline_version: str = "1.0.0",
                 enable_ocr: bool = True,
                 enable_nlp: bool = True,
                 min_chunk_size: int = 100,
                 max_chunk_size: int = 1000,
                 overlap_size: int = 50,
                 quality_threshold: float = 0.7):
        """
        Initialize the advanced PDF processor.
        
        Args:
            pipeline_version: Version identifier for tracking
            enable_ocr: Whether to use OCR for image-based content
            enable_nlp: Whether to use NLP for advanced analysis
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
            overlap_size: Overlap between adjacent chunks
            quality_threshold: Minimum quality score for chunks
        """
        self.pipeline_version = pipeline_version
        self.enable_ocr = enable_ocr and OCR_AVAILABLE
        self.enable_nlp = enable_nlp and NLP_AVAILABLE
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.quality_threshold = quality_threshold
        
        # Initialize NLP components if available
        self.nlp = None
        self.summarizer = None
        if self.enable_nlp:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                logger.info("NLP components initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize NLP components: {e}")
                self.enable_nlp = False
        
        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "ocr_pages": 0,
            "quality_rejections": 0,
            "average_quality_score": 0.0
        }
        
        logger.info(f"AdvancedPDFProcessor initialized (v{pipeline_version})")
        logger.info(f"OCR enabled: {self.enable_ocr}")
        logger.info(f"NLP enabled: {self.enable_nlp}")
    
    def analyze_document_structure(self, pdf_path: str) -> DocumentStructure:
        """
        Analyze the overall structure of a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DocumentStructure with comprehensive analysis
        """
        logger.info(f"Analyzing document structure: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        # Extract text for analysis
        full_text = ""
        table_count = 0
        figure_count = 0
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            full_text += text + "\n"
            
            # Count tables and figures (basic detection)
            if "table" in text.lower() or "|" in text:
                table_count += 1
            if any(keyword in text.lower() for keyword in ["figure", "fig.", "image", "chart"]):
                figure_count += 1
        
        # Analyze text structure
        has_toc = self._detect_table_of_contents(full_text)
        heading_levels = self._extract_heading_levels(full_text)
        list_count = len(re.findall(r'^\s*[•\-\*\d+\.]\s+', full_text, re.MULTILINE))
        footnote_count = len(re.findall(r'\[\d+\]|\(\d+\)', full_text))
        
        # Estimate document type
        estimated_type = self._classify_document_type(full_text, table_count, figure_count)
        
        # Calculate quality score
        quality_score = self._calculate_text_quality(full_text)
        
        # Detect language (simple heuristic)
        language = self._detect_language(full_text)
        
        doc.close()
        
        structure = DocumentStructure(
            page_count=page_count,
            has_toc=has_toc,
            heading_levels=heading_levels,
            table_count=table_count,
            figure_count=figure_count,
            list_count=list_count,
            footnote_count=footnote_count,
            language=language,
            estimated_type=estimated_type,
            quality_score=quality_score
        )
        
        logger.info(f"Document analysis complete: {estimated_type.value}, quality: {quality_score:.2f}")
        return structure
    
    def extract_text_with_structure(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text with structural information preserved.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of page content with structure information
        """
        logger.info(f"Extracting text with structure: {pdf_path}")
        
        pages_content = []
        
        # Use pdfplumber for better structure detection
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_content = {
                    "page_number": page_num + 1,
                    "text": "",
                    "tables": [],
                    "images": [],
                    "text_blocks": [],
                    "ocr_used": False,
                    "quality_score": 1.0
                }
                
                # Extract main text
                text = page.extract_text()
                if text:
                    page_content["text"] = text
                    page_content["quality_score"] = self._calculate_text_quality(text)
                else:
                    # Fallback to OCR if no text found
                    if self.enable_ocr:
                        text = self._extract_text_with_ocr(pdf_path, page_num)
                        page_content["text"] = text
                        page_content["ocr_used"] = True
                        page_content["quality_score"] = 0.8  # Lower quality for OCR
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    page_content["tables"] = [self._format_table(table) for table in tables]
                
                # Extract text blocks with positioning
                page_content["text_blocks"] = self._extract_text_blocks(page)
                
                pages_content.append(page_content)
        
        logger.info(f"Extracted content from {len(pages_content)} pages")
        return pages_content
    
    def create_hierarchical_chunks(self, 
                                 pages_content: List[Dict[str, Any]], 
                                 doc_structure: DocumentStructure,
                                 pdf_path: str) -> List[ProcessedChunk]:
        """
        Create hierarchical chunks with advanced context preservation.
        
        Args:
            pages_content: Extracted page content
            doc_structure: Document structure analysis
            pdf_path: Original PDF path
            
        Returns:
            List of processed chunks with comprehensive metadata
        """
        logger.info("Creating hierarchical chunks with context preservation")
        
        chunks = []
        doc_id = self._generate_doc_id(pdf_path)
        source_file = os.path.basename(pdf_path)
        current_section_hierarchy = []
        
        chunk_index = 0
        
        for page_content in pages_content:
            page_num = page_content["page_number"]
            text = page_content["text"]
            
            if not text.strip():
                continue
            
            # Detect sections and headings
            sections = self._detect_sections(text, doc_structure)
            
            for section in sections:
                # Update section hierarchy
                if section["is_heading"]:
                    self._update_section_hierarchy(current_section_hierarchy, section)
                
                # Create chunks for this section
                section_chunks = self._create_adaptive_chunks(
                    section["content"],
                    doc_structure.estimated_type,
                    section["content_type"]
                )
                
                for i, chunk_text in enumerate(section_chunks):
                    if len(chunk_text.strip()) < self.min_chunk_size:
                        continue
                    
                    # Calculate quality score
                    quality_score = self._calculate_text_quality(chunk_text)
                    if quality_score < self.quality_threshold:
                        self.stats["quality_rejections"] += 1
                        continue
                    
                    # Create comprehensive metadata
                    metadata = self._create_chunk_metadata(
                        chunk_index=chunk_index,
                        doc_id=doc_id,
                        source_file=source_file,
                        page_number=page_num,
                        text=chunk_text,
                        section_hierarchy=current_section_hierarchy.copy(),
                        chunk_type=section["content_type"],
                        quality_score=quality_score,
                        ocr_confidence=page_content.get("quality_score", 1.0)
                    )
                    
                    chunk = ProcessedChunk(
                        text=chunk_text,
                        metadata=metadata
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
        
        # Add chunk relationships
        self._add_chunk_relationships(chunks)
        
        # Update statistics
        self.stats["documents_processed"] += 1
        self.stats["chunks_created"] += len(chunks)
        self.stats["average_quality_score"] = (
            sum(chunk.metadata.text_quality_score for chunk in chunks) / len(chunks)
            if chunks else 0
        )
        
        logger.info(f"Created {len(chunks)} hierarchical chunks")
        return chunks
    
    def process_pdf(self, pdf_path: str) -> Tuple[List[ProcessedChunk], DocumentStructure]:
        """
        Complete PDF processing pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (processed chunks, document structure)
        """
        logger.info(f"Starting complete PDF processing: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Step 1: Analyze document structure
        doc_structure = self.analyze_document_structure(pdf_path)
        
        # Step 2: Extract text with structure
        pages_content = self.extract_text_with_structure(pdf_path)
        
        # Step 3: Create hierarchical chunks
        chunks = self.create_hierarchical_chunks(pages_content, doc_structure, pdf_path)
        
        logger.info(f"PDF processing complete: {len(chunks)} chunks created")
        return chunks, doc_structure
    
    def evaluate_processing_quality(self, chunks: List[ProcessedChunk]) -> Dict[str, Any]:
        """
        Evaluate the quality of the PDF processing results.
        
        Args:
            chunks: Processed chunks to evaluate
            
        Returns:
            Quality evaluation metrics
        """
        if not chunks:
            return {"error": "No chunks to evaluate"}
        
        # Calculate metrics
        total_chunks = len(chunks)
        avg_chunk_length = sum(len(chunk.text) for chunk in chunks) / total_chunks
        avg_quality_score = sum(chunk.metadata.text_quality_score for chunk in chunks) / total_chunks
        
        # Content type distribution
        content_types = {}
        for chunk in chunks:
            chunk_type = chunk.metadata.chunk_type.value
            content_types[chunk_type] = content_types.get(chunk_type, 0) + 1
        
        # Quality distribution
        quality_ranges = {"high": 0, "medium": 0, "low": 0}
        for chunk in chunks:
            score = chunk.metadata.text_quality_score
            if score >= 0.8:
                quality_ranges["high"] += 1
            elif score >= 0.6:
                quality_ranges["medium"] += 1
            else:
                quality_ranges["low"] += 1
        
        return {
            "total_chunks": total_chunks,
            "average_chunk_length": avg_chunk_length,
            "average_quality_score": avg_quality_score,
            "content_type_distribution": content_types,
            "quality_distribution": quality_ranges,
            "processing_stats": self.stats.copy()
        }
    
    # Helper methods (implementation details)
    
    def _detect_table_of_contents(self, text: str) -> bool:
        """Detect if document has a table of contents."""
        toc_indicators = [
            "table of contents", "contents", "index",
            r"\.\.\.\.\.", r"\d+\s*$"  # Page numbers with dots
        ]
        return any(re.search(pattern, text.lower()) for pattern in toc_indicators)
    
    def _extract_heading_levels(self, text: str) -> List[int]:
        """Extract detected heading levels."""
        # Simple heuristic for heading detection
        lines = text.split('\n')
        heading_levels = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for numbered headings (1., 1.1., etc.)
            if re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', line):
                level = len(re.findall(r'\.', line.split()[0])) + 1
                if level not in heading_levels:
                    heading_levels.append(level)
        
        return sorted(heading_levels)
    
    def _classify_document_type(self, text: str, table_count: int, figure_count: int) -> DocumentType:
        """Classify document type based on content analysis."""
        text_lower = text.lower()
        
        # Academic indicators
        academic_keywords = ["abstract", "introduction", "methodology", "conclusion", "references", "bibliography"]
        academic_score = sum(1 for keyword in academic_keywords if keyword in text_lower)
        
        # Technical indicators
        technical_keywords = ["specification", "manual", "procedure", "installation", "configuration"]
        technical_score = sum(1 for keyword in technical_keywords if keyword in text_lower)
        
        # Form indicators
        if table_count > len(text.split('\n')) * 0.3:  # High table density
            return DocumentType.FORM
        
        if academic_score >= 3:
            return DocumentType.ACADEMIC
        elif technical_score >= 2:
            return DocumentType.TECHNICAL
        elif figure_count > 0 and table_count > 0:
            return DocumentType.MIXED
        elif len(re.findall(r'^\d+\.', text, re.MULTILINE)) > 5:
            return DocumentType.STRUCTURED
        else:
            return DocumentType.UNSTRUCTURED
    
    def _calculate_text_quality(self, text: str) -> float:
        """Calculate text quality score (0-1)."""
        if not text.strip():
            return 0.0
        
        # Basic quality indicators
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        space_chars = sum(1 for c in text if c.isspace())
        
        if total_chars == 0:
            return 0.0
        
        # Quality metrics
        alpha_ratio = alpha_chars / total_chars
        space_ratio = space_chars / total_chars
        
        # Penalize too many special characters or poor formatting
        quality_score = alpha_ratio * 0.7 + min(space_ratio * 4, 0.3)
        
        # Bonus for proper sentence structure
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 1:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 5 <= avg_sentence_length <= 50:  # Reasonable sentence length
                quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _detect_language(self, text: str) -> str:
        """Detect document language (simple heuristic)."""
        # Simple language detection based on common words
        italian_words = ["il", "la", "di", "per", "con", "del", "della", "che", "corso", "università"]
        english_words = ["the", "and", "of", "to", "for", "with", "course", "university"]
        
        text_lower = text.lower()
        italian_count = sum(1 for word in italian_words if f" {word} " in text_lower)
        english_count = sum(1 for word in english_words if f" {word} " in text_lower)
        
        return "it" if italian_count > english_count else "en"
    
    def _extract_text_with_ocr(self, pdf_path: str, page_num: int) -> str:
        """Extract text using OCR for image-based pages."""
        if not self.enable_ocr:
            return ""
        
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # OCR with configuration for better accuracy
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(img, config=custom_config)
            
            doc.close()
            self.stats["ocr_pages"] += 1
            return text
            
        except Exception as e:
            logger.warning(f"OCR failed for page {page_num}: {e}")
            return ""
    
    def _format_table(self, table: List[List[str]]) -> Dict[str, Any]:
        """Format extracted table data."""
        if not table:
            return {}
        
        return {
            "rows": len(table),
            "columns": len(table[0]) if table else 0,
            "data": table,
            "text_representation": "\n".join([
                "\t".join([str(cell) if cell is not None else "" for cell in row]) 
                for row in table if row
            ])
        }
    
    def _extract_text_blocks(self, page) -> List[Dict[str, Any]]:
        """Extract text blocks with positioning information."""
        text_blocks = []
        
        try:
            chars = page.chars
            if not chars:
                return text_blocks
            
            # Group characters into text blocks (simplified)
            current_block = {
                "text": "",
                "bbox": None,
                "font_size": None,
                "font_name": None
            }
            
            for char in chars:
                if current_block["text"] == "":
                    current_block["bbox"] = [char["x0"], char["top"], char["x1"], char["bottom"]]
                    current_block["font_size"] = char.get("size", 12)
                    current_block["font_name"] = char.get("fontname", "unknown")
                
                current_block["text"] += char["text"]
                
                # End block on line break or significant font change
                if char["text"] == "\n" or len(current_block["text"]) > 500:
                    if current_block["text"].strip():
                        text_blocks.append(current_block.copy())
                    current_block = {"text": "", "bbox": None, "font_size": None, "font_name": None}
            
            # Add final block
            if current_block["text"].strip():
                text_blocks.append(current_block)
                
        except Exception as e:
            logger.warning(f"Could not extract text blocks: {e}")
        
        return text_blocks
    
    def _detect_sections(self, text: str, doc_structure: DocumentStructure) -> List[Dict[str, Any]]:
        """Detect sections and their types in the text."""
        sections = []
        lines = text.split('\n')
        
        current_section = {
            "content": "",
            "is_heading": False,
            "content_type": ChunkType.PARAGRAPH,
            "heading_level": None
        }
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                if current_section["content"]:
                    current_section["content"] += "\n"
                continue
            
            # Detect headings
            is_heading, level = self._is_heading(line_stripped)
            
            if is_heading:
                # Save previous section
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                current_section = {
                    "content": line_stripped,
                    "is_heading": True,
                    "content_type": ChunkType.HEADING,
                    "heading_level": level
                }
                sections.append(current_section.copy())
                
                # Reset for content after heading
                current_section = {
                    "content": "",
                    "is_heading": False,
                    "content_type": ChunkType.PARAGRAPH,
                    "heading_level": None
                }
            else:
                # Detect content type
                content_type = self._detect_content_type(line_stripped)
                
                if content_type != current_section["content_type"] and current_section["content"]:
                    # Content type changed, save current section
                    sections.append(current_section.copy())
                    current_section = {
                        "content": line_stripped,
                        "is_heading": False,
                        "content_type": content_type,
                        "heading_level": None
                    }
                else:
                    current_section["content"] += "\n" + line_stripped
                    current_section["content_type"] = content_type
        
        # Add final section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def _is_heading(self, line: str) -> Tuple[bool, Optional[int]]:
        """Determine if a line is a heading and its level."""
        # Numbered headings (1., 1.1., etc.)
        numbered_match = re.match(r'^(\d+(\.\d+)*\.?)\s+([A-Z].*)', line)
        if numbered_match:
            level = len(numbered_match.group(1).split('.'))
            return True, level
        
        # All caps short lines (likely headings)
        if line.isupper() and len(line) < 100 and len(line.split()) < 15:
            return True, 1
        
        # Title case short lines
        if line.istitle() and len(line) < 80 and len(line.split()) < 12:
            return True, 2
        
        return False, None
    
    def _detect_content_type(self, line: str) -> ChunkType:
        """Detect the type of content in a line."""
        # List items
        if re.match(r'^\s*[•\-\*\d+\.]\s+', line):
            return ChunkType.LIST
        
        # Table-like content
        if '|' in line or '\t' in line:
            return ChunkType.TABLE
        
        # Figure captions
        if re.match(r'^(Figure|Fig\.|Figura)\s+\d+', line, re.IGNORECASE):
            return ChunkType.FIGURE_CAPTION
        
        # Headers/footers (simple heuristic)
        if len(line) < 50 and (
            any(keyword in line.lower() for keyword in ['page', 'pagina', 'chapter', 'capitolo']) or
            re.search(r'\d+$', line.strip())  # Ends with page number
        ):
            return ChunkType.FOOTER
        
        return ChunkType.PARAGRAPH
    
    def _update_section_hierarchy(self, hierarchy: List[str], section: Dict[str, Any]):
        """Update the section hierarchy based on current section."""
        if not section["is_heading"]:
            return
        
        level = section["heading_level"] or 1
        title = section["content"] or "Untitled Section"
        
        # Ensure title is a string and not None
        if title is None:
            title = "Untitled Section"
        
        # Adjust hierarchy based on heading level
        if level == 1:
            hierarchy.clear()
            hierarchy.append(title)
        elif level <= len(hierarchy):
            hierarchy[:level-1] = hierarchy[:level-1]
            if level <= len(hierarchy):
                hierarchy[level-1] = title
            else:
                hierarchy.append(title)
        else:
            hierarchy.append(title)
    
    def _create_adaptive_chunks(self, 
                               content: str, 
                               doc_type: DocumentType, 
                               content_type: ChunkType) -> List[str]:
        """Create chunks using adaptive strategies based on content type."""
        if not content.strip():
            return []
        
        # Different chunking strategies based on content type
        if content_type == ChunkType.HEADING:
            return [content]  # Headings are single chunks
        
        elif content_type == ChunkType.LIST:
            return self._chunk_list_content(content)
        
        elif content_type == ChunkType.TABLE:
            return [content]  # Tables should stay together
        
        elif doc_type == DocumentType.ACADEMIC:
            return self._chunk_academic_content(content)
        
        else:
            return self._chunk_general_content(content)
    
    def _chunk_list_content(self, content: str) -> List[str]:
        """Chunk list content preserving list structure."""
        lines = content.split('\n')
        chunks = []
        current_chunk = ""
        
        for line in lines:
            if re.match(r'^\s*[•\-\*\d+\.]\s+', line):
                # New list item
                if current_chunk and len(current_chunk) > self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                elif current_chunk:
                    current_chunk += '\n' + line
                else:
                    current_chunk = line
            else:
                current_chunk += '\n' + line
            
            # Check max size
            if len(current_chunk) > self.max_chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_academic_content(self, content: str) -> List[str]:
        """Chunk academic content with sentence-aware splitting."""
        if self.enable_nlp and self.nlp:
            return self._chunk_with_nlp(content)
        else:
            return self._chunk_by_sentences(content)
    
    def _chunk_with_nlp(self, content: str) -> List[str]:
        """Use NLP for intelligent chunking."""
        doc = self.nlp(content)
        sentences = [sent.text for sent in doc.sents]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_by_sentences(self, content: str) -> List[str]:
        """Chunk by sentences using regex."""
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_general_content(self, content: str) -> List[str]:
        """General chunking strategy for unstructured content."""
        words = content.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            current_text = " ".join(current_chunk)
            
            if len(current_text) > self.max_chunk_size:
                # Find last sentence boundary
                chunk_text = " ".join(current_chunk[:-1])
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)
                    current_chunk = [word]
                else:
                    # Force split if no sentence boundary
                    chunks.append(current_text)
                    current_chunk = []
        
        if current_chunk:
            final_text = " ".join(current_chunk)
            if len(final_text) >= self.min_chunk_size:
                chunks.append(final_text)
        
        return chunks
    
    def _generate_doc_id(self, pdf_path: str) -> str:
        """Generate unique document ID."""
        file_name = os.path.basename(pdf_path)
        return hashlib.md5(file_name.encode()).hexdigest()[:12]
    
    def _create_chunk_metadata(self, **kwargs) -> ChunkMetadata:
        """Create comprehensive chunk metadata."""
        from datetime import datetime
        
        text = kwargs["text"]
        
        return ChunkMetadata(
            chunk_id=f"{kwargs['doc_id']}_chunk_{kwargs['chunk_index']:04d}",
            doc_id=kwargs["doc_id"],
            source_file=kwargs["source_file"],
            page_number=kwargs["page_number"],
            chunk_index=kwargs["chunk_index"],
            char_start=0,  # Would need position tracking for exact values
            char_end=len(text),
            chunk_type=kwargs["chunk_type"],
            heading_level=kwargs.get("heading_level"),
            parent_section=kwargs["section_hierarchy"][-1] if kwargs["section_hierarchy"] else None,
            section_hierarchy=kwargs["section_hierarchy"],
            text_length=len(text),
            token_count=len(text.split()),  # Approximate token count
            language=self._detect_language(text),
            reading_level=self._calculate_reading_level(text),
            ocr_confidence=kwargs.get("ocr_confidence"),
            text_quality_score=kwargs["quality_score"],
            predecessor_id=None,  # Set in post-processing
            successor_id=None,    # Set in post-processing
            related_chunks=[],    # Set in post-processing
            embedding_model=None,
            embedding_dimension=None,
            processing_timestamp=datetime.now().isoformat(),
            pipeline_version=self.pipeline_version
        )
    
    def _calculate_reading_level(self, text: str) -> float:
        """Calculate reading level (simplified)."""
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum(self._count_syllables(word) for word in text.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch Reading Ease score
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return max(0.0, min(100.0, score)) / 100.0  # Normalize to 0-1
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)."""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _add_chunk_relationships(self, chunks: List[ProcessedChunk]):
        """Add predecessor/successor relationships between chunks."""
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.metadata.predecessor_id = chunks[i-1].metadata.chunk_id
            if i < len(chunks) - 1:
                chunk.metadata.successor_id = chunks[i+1].metadata.chunk_id

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) != 2:
        print("Usage: python advanced_pdf_processor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Initialize processor
    processor = AdvancedPDFProcessor(
        enable_ocr=True,
        enable_nlp=True,
        min_chunk_size=150,
        max_chunk_size=800,
        quality_threshold=0.6
    )
    
    # Process PDF
    try:
        chunks, structure = processor.process_pdf(pdf_path)
        
        print(f"\n📄 Document Analysis:")
        print(f"   Type: {structure.estimated_type.value}")
        print(f"   Pages: {structure.page_count}")
        print(f"   Quality: {structure.quality_score:.2f}")
        print(f"   Language: {structure.language}")
        
        print(f"\n📦 Chunks Created: {len(chunks)}")
        
        # Evaluate quality
        quality_metrics = processor.evaluate_processing_quality(chunks)
        print(f"\n📊 Quality Metrics:")
        print(f"   Average chunk length: {quality_metrics['average_chunk_length']:.0f}")
        print(f"   Average quality score: {quality_metrics['average_quality_score']:.2f}")
        print(f"   Content types: {quality_metrics['content_type_distribution']}")
        
        # Show sample chunks
        print(f"\n📝 Sample Chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"   Chunk {i+1}: {chunk.text[:100]}...")
            print(f"   Type: {chunk.metadata.chunk_type.value}")
            print(f"   Quality: {chunk.metadata.text_quality_score:.2f}")
            print()
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)

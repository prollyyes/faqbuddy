#!/usr/bin/env python3
"""
Web Search Enhancer for RAG v2
==============================

This module enhances RAG v2 responses by performing web searches with a Sapienza bias
to provide more accurate and up-to-date information.
"""

import os
import time
import re
import requests
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote_plus, urlparse
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class WebSearchResult:
    """Structured web search result."""
    title: str
    url: str
    snippet: str
    source: str  # 'sapienza', 'general', 'academic'
    relevance_score: float
    content_type: str  # 'official', 'news', 'academic', 'student'

class WebSearchEnhancer:
    """
    Web search enhancer with Sapienza bias for RAG v2.
    
    Features:
    - Sapienza-specific search queries
    - Multiple search engines (Google, Bing, DuckDuckGo)
    - Content filtering and relevance scoring
    - Integration with RAG v2 pipeline
    """
    
    def __init__(self):
        """Initialize the web search enhancer."""
        self.sapienza_keywords = [
            'Sapienza', 'Università di Roma', 'La Sapienza', 'Sapienza University of Rome',
            'Sapienza Roma', 'UniRoma1', 'Sapienza Università di Roma'
        ]
        
        self.sapienza_domains = [
            'uniroma1.it', 'sapienza.uniroma1.it', 'studenti.uniroma1.it',
            'web.uniroma1.it', 'www.uniroma1.it'
        ]
        
        # Search engine configurations
        self.search_engines = {
            'google': {
                'enabled': True,
                'api_key': os.getenv('GOOGLE_SEARCH_API_KEY'),
                'cx': os.getenv('GOOGLE_SEARCH_CX')
            },
            'bing': {
                'enabled': True,
                'api_key': os.getenv('BING_SEARCH_API_KEY')
            },
            'duckduckgo': {
                'enabled': True,
                'api_key': None  # No API key needed
            }
        }
        
        print("[WEB] Web Search Enhancer initialized")
        print(f"   Sapienza keywords: {len(self.sapienza_keywords)}")
        print(f"   Sapienza domains: {len(self.sapienza_domains)}")
        print(f"   Search engines: {list(self.search_engines.keys())}")
    
    def _extract_essential_keywords(self, query: str) -> str:
        """
        Extract essential keywords from the query, keeping important function words.
        
        Args:
            query: Original query
            
        Returns:
            Essential keywords for search
        """
        # Important function words to KEEP (these add context to the search)
        important_function_words = {
            'come', 'quando', 'dove', 'perché', 'quanto', 'quale', 'chi', 'cosa',
            'funziona', 'funzionano', 'funzionare', 'lavora', 'lavorano', 'lavorare',
            'trova', 'trovare', 'cerca', 'cercare', 'mostra', 'mostrare'
        }
        
        # Common Italian stop words to remove (noise words)
        stop_words = {
            'mi', 'ti', 'ci', 'vi', 'si', 'lo', 'la', 'li', 'le', 'gli', 'ne',
            'spieghi', 'spiega', 'spiegare', 'dimmi', 'dirmi', 'sai', 'conosci',
            'vorrei', 'potresti', 'puoi', 'posso', 'devo', 'bisogna',
            'il', 'la', 'lo', 'gli', 'le', 'un', 'una', 'uno', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
            'e', 'o', 'ma', 'se', 'che',
            'questo', 'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle',
            'mio', 'mia', 'miei', 'mie', 'tuo', 'tua', 'tuoi', 'tue', 'suo', 'sua', 'suoi', 'sue',
            'nostro', 'nostra', 'nostri', 'nostre', 'vostro', 'vostra', 'vostri', 'vostre',
            'loro'
        }
        
        # Remove punctuation and split into words
        import re
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter words: keep important function words and content words, remove noise
        essential_words = []
        for word in words:
            # Keep important function words regardless of length
            if word in important_function_words:
                essential_words.append(word)
            # Keep content words that are not stop words and have sufficient length
            elif word not in stop_words and len(word) >= 3:
                essential_words.append(word)
        
        # Join back into a string
        essential_query = ' '.join(essential_words)
        
        return essential_query
    
    def _enhance_query_for_sapienza(self, query: str) -> str:
        """
        Enhance query with Sapienza-specific terms.
        
        Args:
            query: Original query
            
        Returns:
            Enhanced query with Sapienza bias
        """
        # Extract essential keywords first
        essential_query = self._extract_essential_keywords(query)
        
        # Add Sapienza context if not already present
        query_lower = essential_query.lower()
        has_sapienza = any(keyword.lower() in query_lower for keyword in self.sapienza_keywords)
        
        if not has_sapienza:
            # ALWAYS add Sapienza context - this was the issue!
            # Add specific context based on query type, but always include Sapienza
            if any(word in query_lower for word in ['corso', 'insegnante', 'professore', 'docente', 'materia', 'lezione']):
                enhanced_query = f"{essential_query} Sapienza Università di Roma corso"
            elif any(word in query_lower for word in ['iscrizione', 'ammissione', 'requisiti', 'immatricolazione']):
                enhanced_query = f"{essential_query} Sapienza Università di Roma iscrizione"
            elif any(word in query_lower for word in ['esame', 'esami', 'laurea', 'diploma', 'tesi']):
                enhanced_query = f"{essential_query} Sapienza Università di Roma esami"
            elif any(word in query_lower for word in ['orario', 'aula', 'aule', 'sede', 'edificio']):
                enhanced_query = f"{essential_query} Sapienza Università di Roma campus"
            elif any(word in query_lower for word in ['tasse', 'quota', 'costo', 'prezzo', 'pagamento']):
                enhanced_query = f"{essential_query} Sapienza Università di Roma tasse"
            else:
                enhanced_query = f"{essential_query} Sapienza Università di Roma"
        else:
            # Even if Sapienza is mentioned, ensure it's properly formatted
            enhanced_query = essential_query
            
        print(f"[SEARCH] Web search enhanced query: '{query}' -> '{enhanced_query}'")
        
        return enhanced_query
    
    def _search_google(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Search using Google Custom Search API."""
        if not self.search_engines['google']['enabled'] or not self.search_engines['google']['api_key']:
            return []
        
        try:
            api_key = self.search_engines['google']['api_key']
            cx = self.search_engines['google']['cx']
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'num': min(max_results, 10)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                result = WebSearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    snippet=item.get('snippet', ''),
                    source=self._classify_source(item.get('link', '')),
                    relevance_score=self._calculate_relevance_score(item, query),
                    content_type=self._classify_content_type(item)
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"[WARN] Google search failed: {e}")
            return []
    
    
    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Search using DuckDuckGo Instant Answer API."""
        if not self.search_engines['duckduckgo']['enabled']:
            return []
        
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Process related topics
            for topic in data.get('RelatedTopics', [])[:max_results]:
                if isinstance(topic, dict) and 'Text' in topic:
                    result = WebSearchResult(
                        title=topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                        url=topic.get('FirstURL', ''),
                        snippet=topic.get('Text', ''),
                        source=self._classify_source(topic.get('FirstURL', '')),
                        relevance_score=self._calculate_relevance_score(topic, query),
                        content_type=self._classify_content_type(topic)
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"[WARN] DuckDuckGo search failed: {e}")
            return []
    
    def _classify_source(self, url: str) -> str:
        """Classify the source of a search result."""
        if not url:
            return 'general'
        
        domain = urlparse(url).netloc.lower()
        
        # Check if it's a Sapienza domain
        if any(sapienza_domain in domain for sapienza_domain in self.sapienza_domains):
            return 'sapienza'
        
        # Check if it's an academic domain
        academic_domains = ['.edu', '.ac.', 'university', 'università', 'uniroma']
        if any(academic in domain for academic in academic_domains):
            return 'academic'
        
        return 'general'
    
    def _classify_content_type(self, item: Dict[str, Any]) -> str:
        """Classify the content type of a search result."""
        url = item.get('url', item.get('link', item.get('FirstURL', '')))
        title = item.get('title', item.get('name', item.get('Text', '')))
        
        if not url:
            return 'general'
        
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Official Sapienza content
        if any(domain in url_lower for domain in self.sapienza_domains):
            if any(word in url_lower for word in ['regolamento', 'norme', 'procedure']):
                return 'official'
            elif any(word in url_lower for word in ['news', 'notizie', 'comunicati']):
                return 'news'
            else:
                return 'official'
        
        # Academic content
        if any(word in url_lower for word in ['.edu', 'research', 'paper', 'academic']):
            return 'academic'
        
        # Student content
        if any(word in title_lower for word in ['student', 'studente', 'forum', 'reddit']):
            return 'student'
        
        return 'general'
    
    def _calculate_relevance_score(self, item: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a search result."""
        title = item.get('title', item.get('name', item.get('Text', '')))
        snippet = item.get('snippet', item.get('Text', ''))
        url = item.get('url', item.get('link', item.get('FirstURL', '')))
        
        score = 0.0
        
        # Base score from source classification
        source = self._classify_source(url)
        if source == 'sapienza':
            score += 0.8
        elif source == 'academic':
            score += 0.6
        else:
            score += 0.3
        
        # Content type bonus
        content_type = self._classify_content_type(item)
        if content_type == 'official':
            score += 0.2
        elif content_type == 'academic':
            score += 0.1
        
        # Query term matching
        query_terms = query.lower().split()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        for term in query_terms:
            if term in title_lower:
                score += 0.1
            if term in snippet_lower:
                score += 0.05
        
        # Sapienza keyword bonus
        for keyword in self.sapienza_keywords:
            if keyword.lower() in title_lower or keyword.lower() in snippet_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """
        Perform web search with Sapienza bias.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of web search results
        """
        start_time = time.time()
        
        # Enhance query for Sapienza
        enhanced_query = self._enhance_query_for_sapienza(query)
        print(f"[SEARCH] Web search: '{query}' → '{enhanced_query}'")
        
        # Search across multiple engines
        all_results = []
        
        # Google search
        google_results = self._search_google(enhanced_query, max_results)
        all_results.extend(google_results)
        
        
        # DuckDuckGo search
        ddg_results = self._search_duckduckgo(enhanced_query, max_results)
        all_results.extend(ddg_results)
        
        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_results(all_results)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Take top results
        final_results = unique_results[:max_results]
        
        search_time = time.time() - start_time
        print(f"[OK] Web search completed in {search_time:.3f}s")
        print(f"[DATA] Found {len(final_results)} results")
        
        # Log result breakdown
        source_counts = {}
        for result in final_results:
            source_counts[result.source] = source_counts.get(result.source, 0) + 1
        print(f"   Source breakdown: {source_counts}")
        
        return final_results
    
    def _deduplicate_results(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """Remove duplicate results based on URL and title similarity."""
        seen_urls = set()
        seen_titles = set()
        unique_results = []
        
        for result in results:
            # Normalize URL
            url = result.url.lower().rstrip('/')
            
            # Normalize title
            title = re.sub(r'\s+', ' ', result.title.lower().strip())
            
            # Check for duplicates
            if url not in seen_urls and title not in seen_titles:
                seen_urls.add(url)
                seen_titles.add(title)
                unique_results.append(result)
        
        return unique_results
    
    def format_results_for_rag(self, results: List[WebSearchResult]) -> List[Dict[str, Any]]:
        """
        Format web search results for integration with RAG v2.
        
        Args:
            results: List of web search results
            
        Returns:
            List of formatted results compatible with RAG v2
        """
        formatted_results = []
        
        for i, result in enumerate(results, 1):
            formatted_result = {
                'id': f'web_search_{i}',
                'score': result.relevance_score,
                'metadata': {
                    'source': 'web_search',
                    'url': result.url,
                    'title': result.title,
                    'source_type': result.source,
                    'content_type': result.content_type,
                    'search_engine': 'multiple'
                },
                'namespace': 'web_search',
                'text': f"Titolo: {result.title}\n\n{result.snippet}\n\nFonte: {result.url}"
            }
            formatted_results.append(formatted_result)
        
        return formatted_results


def test_web_search_enhancer():
    """Test the web search enhancer."""
    print("🧪 Testing Web Search Enhancer...")
    
    enhancer = WebSearchEnhancer()
    
    # Test queries
    test_queries = [
        "Chi insegna il corso di Sistemi Operativi?",
        "Come si richiede l'iscrizione al corso di laurea?",
        "Quali sono i requisiti per l'ammissione?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print(f"{'='*60}")
        
        results = enhancer.search(query, max_results=3)
        
        print(f"\nResults: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result.source}] {result.title}")
            print(f"     URL: {result.url}")
            print(f"     Score: {result.relevance_score:.3f}")
            print(f"     Type: {result.content_type}")
            print(f"     Snippet: {result.snippet[:100]}...")
            print()
    
    return True


if __name__ == "__main__":
    test_web_search_enhancer() 
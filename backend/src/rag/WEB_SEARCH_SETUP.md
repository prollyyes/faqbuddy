# Web Search Enhancement Setup Guide

## Overview

The Web Search Enhancement feature adds real-time web search capabilities to RAG v2, with a strong bias towards Sapienza University of Rome content. This provides more accurate and up-to-date information.

## Features

- **Sapienza Bias**: Automatically enhances queries with Sapienza-specific terms
- **Multiple Search Engines**: Google, Bing, and DuckDuckGo for comprehensive results
- **Smart Filtering**: Prioritizes official Sapienza domains and academic content
- **RAG Integration**: Seamlessly integrates with existing RAG v2 pipeline

## Configuration

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Web Search Enhancement
WEB_SEARCH_ENHANCEMENT=true

# Google Custom Search API (Optional)
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_CX=your_custom_search_engine_id_here

# Bing Search API (Optional)
BING_SEARCH_API_KEY=your_bing_api_key_here
```

### 2. API Key Setup

#### Google Custom Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Custom Search API"
4. Create credentials (API Key)
5. Go to [Custom Search Engine](https://cse.google.com/cse/)
6. Create a new search engine
7. Add your API key and search engine ID to `.env`

#### Bing Search API
1. Go to [Microsoft Azure Portal](https://portal.azure.com/)
2. Create a new "Bing Search v7" resource
3. Get your subscription key
4. Add to `.env` as `BING_SEARCH_API_KEY`

### 3. Fallback Mode

If no API keys are configured, the system will use DuckDuckGo (free, no API key required) as a fallback.

## Usage

The web search enhancement is automatically enabled when `WEB_SEARCH_ENHANCEMENT=true`. It will:

1. **Enhance Queries**: Add Sapienza context to user queries
2. **Search Multiple Sources**: Query Google, Bing, and DuckDuckGo
3. **Filter Results**: Prioritize Sapienza and academic content
4. **Integrate with RAG**: Combine web results with local knowledge base

## Example

**User Query**: "Chi insegna Sistemi Operativi?"

**Enhanced Query**: "Chi insegna Sistemi Operativi? Sapienza Università di Roma"

**Results**: 
- Official Sapienza course pages
- Academic profiles
- University announcements
- Student forums (lower priority)

## Source Classification

The system classifies results into:

- **Sapienza**: Official uniroma1.it domains (highest priority)
- **Academic**: .edu, university domains (high priority)
- **General**: Other sources (lower priority)

## Content Types

- **Official**: Regulations, procedures, official announcements
- **News**: University news and communications
- **Academic**: Research papers, academic content
- **Student**: Student forums, unofficial sources

## Performance

- **Search Time**: ~0.5-2 seconds per query
- **Results**: 3-5 most relevant results
- **Integration**: Seamless with existing RAG pipeline

## Troubleshooting

### No Results
- Check API keys are correctly configured
- Verify internet connectivity
- Check if search engines are enabled

### Slow Performance
- Reduce `max_results` parameter
- Disable unused search engines
- Check API rate limits

### API Errors
- Verify API keys are valid
- Check API quotas and billing
- Ensure proper permissions

## Testing

Run the test script to verify setup:

```bash
python test_web_search_integration.py
```

This will test:
- Query enhancement
- Web search functionality
- RAG integration format
- Source classification 
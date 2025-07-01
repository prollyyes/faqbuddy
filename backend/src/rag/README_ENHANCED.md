# Enhanced RAG System for FAQBuddy

## 🚀 Overview

This enhanced RAG (Retrieval-Augmented Generation) system represents a significant improvement over the original implementation, inspired by state-of-the-art approaches from the smallRag repository. The system now provides better performance, accuracy, and configurability while maintaining the existing architecture.

## ✨ Key Improvements

### 🎯 Performance Optimizations
- **Reduced Context Length**: Optimized token limits for faster processing
- **Embedding Caching**: LRU cache for frequently used embeddings
- **Lazy Loading**: Models loaded only when needed
- **Streaming Responses**: Reduced perceived latency
- **Optimized LLM Settings**: Apple Silicon-specific optimizations

### 🧠 Enhanced Retrieval
- **Improved Hybrid Search**: Better fusion of dense and sparse retrieval
- **Dynamic Namespace Boosting**: Context-aware namespace selection
- **Enhanced Cross-Encoder**: Better reranking with fallback handling
- **Query Enhancement**: Intelligent query preprocessing
- **Relevance Filtering**: Minimum relevance thresholds

### 📝 Better Prompt Engineering
- **Structured Prompts**: Clear instructions and formatting
- **Context Optimization**: Smart chunk selection and formatting
- **Query Enhancement**: Automatic query improvement
- **Deduplication**: Enhanced semantic deduplication
- **Token Management**: Optimized context length handling

### ⚙️ Configuration Management
- **Performance Profiles**: Speed, Balanced, and Quality modes
- **Centralized Configuration**: Easy tuning and maintenance
- **Dynamic Profile Switching**: Runtime configuration changes
- **Comprehensive Monitoring**: Detailed performance tracking

## 🏗️ Architecture

### Core Components

```
Enhanced RAG System
├── RAGPipeline (Enhanced)
│   ├── Performance Tracking
│   ├── Error Handling
│   └── Component Testing
├── Hybrid Retrieval (Improved)
│   ├── Embedding Caching
│   ├── Dynamic Boosting
│   ├── Enhanced Fusion
│   └── Cross-Encoder Reranking
├── Prompt Building (Enhanced)
│   ├── Query Enhancement
│   ├── Context Optimization
│   ├── Structured Formatting
│   └── Token Management
├── LLM Integration (Optimized)
│   ├── Apple Silicon Support
│   ├── Performance Settings
│   ├── Error Handling
│   └── Streaming Support
└── Configuration System
    ├── Performance Profiles
    ├── Centralized Settings
    ├── Dynamic Updates
    └── Monitoring Tools
```

## 🚀 Quick Start

### 1. Basic Usage

```python
from src.rag.rag_adapter import RAGSystem

# Initialize with balanced profile (default)
rag = RAGSystem()

# Generate response
response = rag.generate_response("Quanti CFU ha il corso di Informatica?")
print(response["response"])
print(f"Time: {response['total_time']:.3f}s")
```

### 2. Performance Profiles

```python
# Speed-optimized profile
rag_speed = RAGSystem(profile="speed")

# Quality-optimized profile
rag_quality = RAGSystem(profile="quality")

# Custom configuration
custom_config = {
    "performance": {"top_k": 6, "use_cross_encoder": False},
    "retrieval": {"alpha": 0.8}
}
rag_custom = RAGSystem(profile="balanced", custom_config=custom_config)
```

### 3. Streaming Responses

```python
# Basic streaming
for token in rag.generate_response_streaming("Come funziona l'iscrizione?"):
    print(token, end="", flush=True)

# Streaming with metadata
for chunk in rag.generate_response_streaming_with_metadata("Quando sono le scadenze?"):
    if chunk["type"] == "token":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "metadata":
        print(f"\nGeneration time: {chunk['generation_time']:.3f}s")
```

## ⚙️ Configuration

### Performance Profiles

#### Speed Profile
- **top_k**: 3 (fewer documents)
- **max_chunks**: 3 (smaller context)
- **use_cross_encoder**: False (faster reranking)
- **alpha**: 0.8 (more dense search weight)
- **llm_temperature**: 0.05 (more deterministic)

#### Balanced Profile (Default)
- **top_k**: 4
- **max_chunks**: 4
- **use_cross_encoder**: True
- **alpha**: 0.7
- **llm_temperature**: 0.1

#### Quality Profile
- **top_k**: 6 (more documents)
- **max_chunks**: 5 (larger context)
- **use_cross_encoder**: True (better reranking)
- **alpha**: 0.6 (balanced approach)
- **llm_temperature**: 0.1

### Custom Configuration

```python
from src.rag.rag_config import update_config

# Custom settings
custom_config = {
    "performance": {
        "top_k": 5,
        "max_chunks": 4,
        "use_cross_encoder": True
    },
    "retrieval": {
        "alpha": 0.75
    },
    "llm": {
        "temperature": 0.15,
        "max_tokens": 800
    }
}

# Apply custom configuration
rag = RAGSystem(profile="balanced", custom_config=custom_config)
```

## 📊 Performance Monitoring

### System Statistics

```python
# Get comprehensive system info
system_info = rag.get_system_info()
print(f"Profile: {system_info['profile']}")
print(f"Top K: {system_info['configuration']['top_k']}")
print(f"Alpha: {system_info['configuration']['alpha']}")

# Get performance stats
stats = rag.get_performance_stats()
print(f"Average retrieval time: {stats['pipeline_stats']['avg_retrieval_time']:.3f}s")
print(f"Success rate: {stats['pipeline_stats']['successful_queries']}/{stats['pipeline_stats']['total_queries']}")
```

### Component Testing

```python
# Test retrieval without generation
retrieval_test = rag.test_retrieval("Quanti CFU ha il corso di Informatica?")
print(f"Intent: {retrieval_test['intent']}")
print(f"Results: {retrieval_test['merged_results_count']}")
print(f"Prompt tokens: {retrieval_test['prompt_metadata']['total_tokens']}")
```

### Performance Testing

```python
from src.rag.performance_test import RAGPerformanceTester

# Run comprehensive performance test
tester = RAGPerformanceTester()
results = tester.run_comprehensive_test()
tester.print_results(results)
tester.save_results(results, "performance_results.json")
```

## 🔧 Advanced Features

### Dynamic Profile Switching

```python
# Switch to speed profile for high-traffic scenarios
switch_result = rag.switch_profile("speed")
if switch_result["success"]:
    print(f"Switched to {switch_result['new_profile']} profile")
    print(f"New top_k: {switch_result['configuration']['top_k']}")
```

### Query Enhancement

The system automatically enhances queries for better retrieval:

```python
# Original query: "Quanti CFU ha il corso di Informatica?"
# Enhanced query: "Quanti CFU ha il corso di Informatica? (contesto universitario) (richiesta informativa)"
```

### Namespace-Aware Retrieval

The system dynamically adjusts namespace boosts based on query content:

- **Document keywords**: regolamento, norme, procedure, esami, lauree, etc.
- **Database keywords**: quali, elenca, lista, corsi, professori, etc.

### Context Optimization

Smart context management for optimal performance:

- **Deduplication**: Removes similar chunks
- **Relevance filtering**: Filters by minimum relevance score
- **Token management**: Optimizes context length
- **Chunk formatting**: Enhanced metadata display

## 🎯 Best Practices

### For Speed Optimization
1. Use the "speed" profile for high-traffic scenarios
2. Disable cross-encoder reranking (`use_cross_encoder=False`)
3. Reduce `top_k` to 3-4 documents
4. Reduce `max_chunks` to 3-4 chunks
5. Increase `alpha` to 0.8 for more dense search weight

### For Quality Optimization
1. Use the "quality" profile for critical queries
2. Enable cross-encoder reranking
3. Increase `top_k` to 5-6 documents
4. Increase `max_chunks` to 5 chunks
5. Use balanced `alpha` (0.6-0.7)

### For Balanced Performance
1. Use the "balanced" profile (default)
2. Monitor performance metrics
3. Adjust settings based on usage patterns
4. Use streaming responses for better UX

## 🔍 Troubleshooting

### Common Issues

#### Slow Performance
```python
# Check current configuration
stats = rag.get_performance_stats()
print(f"Average time: {stats['pipeline_stats']['avg_total_time']:.3f}s")

# Switch to speed profile
rag.switch_profile("speed")

# Check retrieval time
retrieval_test = rag.test_retrieval("test query")
print(f"Retrieval time: {retrieval_test['total_time']:.3f}s")
```

#### Poor Accuracy
```python
# Switch to quality profile
rag.switch_profile("quality")

# Check cross-encoder status
system_info = rag.get_system_info()
print(f"Cross-encoder: {system_info['configuration']['use_cross_encoder']}")
```

#### LLM Issues
```python
# Test LLM connection
from src.utils.llm_mistral import test_llm_connection
llm_test = test_llm_connection()
print(f"LLM Status: {llm_test['status']}")
```

### Performance Monitoring

```python
# Monitor cache performance
retrieval_stats = get_retrieval_stats()
cache_stats = retrieval_stats['cache_stats']
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")

# Monitor embedding model
from src.rag.utils.embeddings import get_embed_model
model = get_embed_model()
print(f"Embedding model: {model}")
```

## 📈 Performance Benchmarks

### Expected Performance (M2 Pro)

| Profile | Avg Response Time | Success Rate | QPM* |
|---------|------------------|--------------|------|
| Speed   | 2-4 seconds      | 85-90%       | 15-30 |
| Balanced| 4-6 seconds      | 90-95%       | 10-15 |
| Quality | 6-8 seconds      | 95-98%       | 7-10  |

*Queries Per Minute

### Component Performance

- **Retrieval**: 0.5-2.0 seconds
- **Prompt Building**: 0.1-0.3 seconds
- **LLM Generation**: 2-6 seconds
- **Cross-Encoder**: 0.5-1.0 seconds (if enabled)

## 🔄 Migration from Original System

The enhanced system is backward compatible. To migrate:

1. **Update imports**:
   ```python
   # Old
   from src.rag.rag_adapter import RAGSystem
   
   # New (same import, enhanced functionality)
   from src.rag.rag_adapter import RAGSystem
   ```

2. **Add configuration** (optional):
   ```python
   # Old
   rag = RAGSystem()
   
   # New (with profile)
   rag = RAGSystem(profile="balanced")
   ```

3. **Use new features** (optional):
   ```python
   # Profile switching
   rag.switch_profile("speed")
   
   # Performance monitoring
   stats = rag.get_performance_stats()
   
   # Component testing
   retrieval_test = rag.test_retrieval("test query")
   ```

## 🎯 Future Enhancements

### Planned Improvements
- **Multi-modal Support**: Image and document understanding
- **Conversation Memory**: Context-aware multi-turn conversations
- **Advanced Reranking**: More sophisticated reranking algorithms
- **Distributed Processing**: Multi-node RAG processing
- **Real-time Updates**: Live document indexing

### Research Areas
- **Query Understanding**: Better intent classification
- **Context Selection**: More intelligent chunk selection
- **Answer Validation**: Confidence scoring for responses
- **Personalization**: User-specific retrieval optimization

## 📚 Additional Resources

- **Configuration Guide**: `rag_config.py`
- **Performance Testing**: `performance_test.py`
- **Component Documentation**: Individual module READMEs
- **API Documentation**: FastAPI docs at `/docs`

---

**Note**: This enhanced RAG system maintains full backward compatibility while providing significant improvements in performance, accuracy, and configurability. The system is designed to be production-ready and can handle high-traffic scenarios with appropriate configuration. 
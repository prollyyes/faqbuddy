# Chat API Documentation

## Unified Chat System

The chat system has been completely unified into a single, intelligent endpoint that automatically chooses the best approach for each question.

### Architecture Overview

- **Single Endpoint**: `/chat` handles all types of questions
- **Automatic Routing**: System decides between T2SQL and RAG automatically
- **Smart Fallback**: If T2SQL fails, automatically falls back to RAG
- **Streaming Support**: Real-time responses for better user experience

## Unified Chat Endpoint

The `/chat` endpoint is the **one and only** endpoint you need for all questions. It automatically:

1. **Analyzes** your question complexity
2. **Tries T2SQL** for simple, structured questions
3. **Falls back to RAG** for complex questions or SQL failures
4. **Supports streaming** for real-time responses

### Endpoint: `POST /chat`

### Request Body
```json
{
  "question": "Your question here"
}
```

### Query Parameters

- `streaming` (optional, boolean, default: `false`): Enable streaming response
- `include_metadata` (optional, boolean, default: `false`): Include metadata in response (only works with streaming)

### Usage Examples

#### 1. Standard Response (Automatic T2SQL/RAG)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the computer science courses?"}'
```

**Possible T2SQL Response:**
```json
{
  "result": [{"nome": "Fondamenti di Informatica", "cfu": 9}],
  "query": "SELECT nome, cfu FROM Corso WHERE nome LIKE '%Informatica%';",
  "natural_response": "I corsi di informatica sono:\n- Fondamenti di Informatica: 9 CFU",
  "chosen": "T2SQL",
  "ml_model": "simple",
  "ml_confidence": 0.85
}
```

**Possible RAG Response:**
```json
{
  "result": "Here are the computer science courses available...",
  "chosen": "RAG",
  "retrieval_time": 0.5,
  "generation_time": 2.1,
  "total_time": 2.6,
  "context_used": 3
}
```

#### 2. Streaming Response
```bash
curl -X POST "http://localhost:8000/chat?streaming=true" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I register for exams?"}'
```

**Response (Server-Sent Events):**
```
data: {"token": "Per", "type": "token"}

data: {"token": " registrarti", "type": "token"}

data: {"token": " agli", "type": "token"}

data: {"token": " esami", "type": "token"}

...

data: {"type": "complete"}
```

#### 3. Streaming Response with Metadata
```bash
curl -X POST "http://localhost:8000/chat?streaming=true&include_metadata=true" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I register for exams?"}'
```

**Response (Server-Sent Events):**
```
data: {"type": "token", "content": "Per", "token_count": 1}

data: {"type": "token", "content": " registrarti", "token_count": 2}

data: {"type": "token", "content": " agli", "token_count": 3}

...

data: {"type": "metadata", "token_count": 45, "finished": true, "intent": "unstructured", "retrieval_method": "unstructured", "context_sources": 5, "namespace_distribution": {"documents": 3, "database": 2}}
```

## How It Works

### Automatic Question Analysis
The system uses machine learning to classify your question:

1. **Simple Questions** → T2SQL (fast, direct database access)
   - "Show me all courses"
   - "What's Professor Rossi's email?"
   - "List courses with 9 CFU"

2. **Complex Questions** → RAG (comprehensive, document-based)
   - "How do I apply for graduation?"
   - "What are the differences between study plans?"
   - "Explain the exam registration process"

### Smart Fallback System
```
Your Question
    ↓
ML Analysis (Simple vs Complex)
    ↓
Simple → Try T2SQL → Success? → Return Result
    ↓                    ↓
    ↓                    ↓
    ↓                 Failure → RAG Fallback
    ↓
Complex → RAG Directly
```

## Response Types

### T2SQL Response
```json
{
  "result": [{"field": "value"}],
  "query": "SELECT * FROM table;",
  "natural_response": "Here are the results...",
  "chosen": "T2SQL",
  "ml_model": "simple",
  "ml_confidence": 0.85
}
```

### RAG Response
```json
{
  "result": "Comprehensive answer with explanations...",
  "chosen": "RAG",
  "retrieval_time": 0.5,
  "generation_time": 2.1,
  "total_time": 2.6,
  "context_used": 3
}
```

### Fallback Response
```json
{
  "result": "Answer from RAG...",
  "chosen": "RAG",
  "fallback_reason": "T2SQL failure",
  "retrieval_time": 0.5,
  "generation_time": 2.1,
  "total_time": 2.6,
  "context_used": 3
}
```

## Error Handling

### Standard Response Error
```json
{
  "error": "Error message here",
  "chosen": "CHAT",
  "result": "Si è verificato un errore durante la generazione della risposta."
}
```

### Streaming Response Error
```
data: {"type": "error", "message": "Error message here"}
```

## Frontend Integration

### JavaScript Example for Standard Chat
```javascript
const response = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ question: 'Your question' })
});

const data = await response.json();
console.log('Answer:', data.result);
console.log('Method used:', data.chosen);
```

### JavaScript Example for Streaming Chat
```javascript
const response = await fetch('/chat?streaming=true', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ question: 'Your question' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      if (data.type === 'token') {
        // Append token to UI
        console.log('Token:', data.token);
      } else if (data.type === 'complete') {
        // Handle completion
        console.log('Streaming complete');
      } else if (data.type === 'error') {
        // Handle error
        console.error('Error:', data.message);
      }
    }
  }
}
```

## Benefits of the Unified Approach

1. **Single Endpoint**: No need to choose between different endpoints
2. **Automatic Optimization**: System picks the best approach automatically
3. **Better User Experience**: Users don't need to understand technical details
4. **Simplified Frontend**: Only one API call to implement
5. **Consistent Responses**: Same response format regardless of method used
6. **Smart Fallback**: Automatic recovery from failures
7. **Streaming Support**: Real-time responses for better UX

## Migration from Old Endpoints

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `POST /t2sql` | `POST /chat` |
| `POST /rag` | `POST /chat` |
| `POST /rag/stream` | `POST /chat?streaming=true` |
| `POST /rag/stream/metadata` | `POST /chat?streaming=true&include_metadata=true` |

## Internal Architecture

### Core Functions
```python
def handle_t2sql_logic(question: str) -> Dict[str, Any]:
    """Handle T2SQL logic with automatic RAG fallback"""

def call_rag_system(question: str, streaming: bool = False, include_metadata: bool = False) -> Any:
    """Unified RAG system call"""

def handle_rag_fallback(question: str, ...) -> Dict[str, Any]:
    """Handle RAG fallback scenarios"""
```

### Flow Diagram
```
Frontend Request → /chat endpoint
    ↓
Question Analysis (ML)
    ↓
Simple Question → T2SQL → Success? → Return
    ↓                    ↓
    ↓                 Failure → RAG
    ↓
Complex Question → RAG Directly
    ↓
Return Unified Response
```

## Summary

The `/chat` endpoint is your **one-stop solution** for all questions. It's like having a smart assistant that:

- **Automatically chooses** the best approach for your question
- **Handles failures gracefully** with automatic fallbacks
- **Provides consistent responses** regardless of the method used
- **Supports real-time streaming** for better user experience

No more confusion about which endpoint to use - just ask your question and let the system handle the rest! 🎉 
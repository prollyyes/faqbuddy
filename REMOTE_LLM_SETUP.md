# Remote LLM Setup Guide

This guide explains how to set up your FAQBuddy pipeline to run models locally while serving your website from the cloud using Ollama and Cloudflare tunnels.

## Overview

The setup allows you to:
- Run LLM models on your local machine with GPU acceleration
- Serve your website from the cloud (e.g., Render)
- Connect the cloud backend to your local models via secure tunnels
- Maintain all FAQBuddy system prompts and functionality

## Prerequisites

- Local machine with GPU (for running models)
- Cloud hosting service (e.g., Render) for your backend
- Ollama installed on your local machine
- Cloudflared installed on your local machine

## Step 1: Install Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the Mistral model
ollama pull mistral:7b-instruct

# Start Ollama server (serves at http://localhost:11434/v1)
ollama serve
```

## Step 2: Set up Cloudflare Tunnel

```bash
# Install cloudflared (if not already installed)
# On Ubuntu/Debian:
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Create tunnel to expose your local Ollama server
cloudflared tunnel --url http://localhost:11434

# Copy the HTTPS URL (e.g., https://abc123.trycloudflare.com)
```

## Step 3: Configure Environment Variables

Set these environment variables on your cloud hosting service (e.g., Render):

```bash
REMOTE_LLM_BASE=https://abc123.trycloudflare.com
REMOTE_LLM_MODEL=mistral:7b-instruct
REMOTE_LLM_API_KEY=none
```

**Note:** Replace `https://abc123.trycloudflare.com` with your actual Cloudflare tunnel URL.

## Step 4: Test the Connection

Use the provided test script to verify everything works:

```bash
# Set environment variables locally for testing
export REMOTE_LLM_BASE="https://abc123.trycloudflare.com"
export REMOTE_LLM_MODEL="mistral:7b-instruct"
export REMOTE_LLM_API_KEY="none"

# Run the test script
python test_remote_llm.py
```

Or test manually with curl:

```bash
curl -sS -X POST "$REMOTE_LLM_BASE/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$REMOTE_LLM_MODEL'",
    "messages": [
      {"role":"system","content":"Sei un assistente utile."},
      {"role":"user","content":"Scrivi solo: ok"}
    ],
    "temperature": 0.1
  }' | jq -r '.choices[0].message.content'
```

## How It Works

### Local Machine
1. **Ollama** runs the Mistral model locally with GPU acceleration
2. **Cloudflared** creates a secure tunnel to expose the Ollama API
3. Models are loaded once and stay in memory for fast responses

### Cloud Backend
1. **Environment variables** tell the backend to use remote LLM
2. **HTTP requests** are sent to your local machine via the tunnel
3. **Responses** are returned with full FAQBuddy formatting and prompts

### Fallback Behavior
- If `REMOTE_LLM_BASE` is not set, the system falls back to local models
- If remote connection fails, appropriate error messages are shown
- All existing functionality is preserved

## Code Changes Made

### llm_mistral.py
- Added remote LLM support with environment variable detection
- Preserved all FAQBuddy system prompts and formatting instructions
- Added `_generate_remote()` function for HTTP API calls
- Updated `generate_answer()` to use remote when available
- Maintained streaming functionality (returns full response for remote)

### llm_gemma.py
- Added remote LLM support for question classification
- Preserved all existing functionality and prompts
- Added remote generation with proper system messages
- Updated streaming to work with remote LLM

## System Prompts Preserved

The following important FAQBuddy characteristics are maintained:

- **University focus**: Only answers university-related questions
- **Professional tone**: Maintains professional but friendly tone
- **Markdown formatting**: Uses proper Markdown with headings, lists, bold, italic
- **Italian language**: Responds in Italian with proper language detection
- **Context awareness**: Uses only provided context, mentions when missing
- **No system tokens**: Cleans response of unwanted tokens

## Troubleshooting

### Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/v1/models

# Check if tunnel is active
# Look for the cloudflared output showing the tunnel URL
```

### Model Issues
```bash
# List available models
ollama list

# Pull model if missing
ollama pull mistral:7b-instruct
```

### Environment Variables
```bash
# Check if variables are set correctly
echo $REMOTE_LLM_BASE
echo $REMOTE_LLM_MODEL
echo $REMOTE_LLM_API_KEY
```

## Performance Considerations

- **Latency**: Remote calls add network latency (~100-500ms)
- **Throughput**: Limited by tunnel bandwidth and local GPU
- **Reliability**: Depends on stable internet connection
- **Cost**: No additional cloud compute costs for LLM inference

## Security Notes

- Cloudflare tunnels are secure and encrypted
- No API keys needed for local Ollama
- Tunnel URLs are temporary and change on restart
- Consider using persistent tunnels for production

## Alternative Models

You can use other Ollama models by changing the model name:

```bash
# Pull different models
ollama pull llama2:7b
ollama pull codellama:7b
ollama pull mistral:7b-instruct

# Update environment variable
REMOTE_LLM_MODEL=llama2:7b
```

## Production Considerations

For production use, consider:
- Using persistent Cloudflare tunnels
- Setting up monitoring for tunnel health
- Implementing retry logic for failed requests
- Using multiple model instances for load balancing
- Setting up proper logging and error handling

## Support

If you encounter issues:
1. Check the test script output for specific error messages
2. Verify all environment variables are set correctly
3. Ensure Ollama and cloudflared are running
4. Check network connectivity between cloud and local machine
5. Review the logs in your cloud hosting service

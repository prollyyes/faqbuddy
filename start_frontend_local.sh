#!/bin/bash

# FAQBuddy Frontend Launcher - Local Development
# =============================================

echo "=========== Starting FAQBuddy Frontend (Local Development) ==========="
echo "=================================================="

# Set environment to use local backend
export NEXT_PUBLIC_USE_LOCAL="true"

echo "🌐 Environment: LOCAL"
echo "🔗 API Host: http://localhost:8000"
echo ""

# Change to frontend directory
cd "$(dirname "$0")/frontend"

echo "=========== Working directory: $(pwd) ==========="
echo "=========== Starting Next.js development server... ==========="
echo ""
echo "=========== Frontend will be available at: http://localhost:3000 ==========="
echo "=========== Backend API: http://localhost:8000 ==========="
echo ""
echo "=========== Press Ctrl+C to stop the server ==========="
echo "--------------------------------------------------"

# Start Next.js development server
npm run dev

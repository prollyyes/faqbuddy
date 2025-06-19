#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Check for required commands
command_exists python3 || handle_error "Python 3 is not installed"
command_exists npm || handle_error "npm is not installed"
command_exists pip3 || handle_error "pip3 is not installed"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Python environment...${NC}"

# Install Python dependencies
pip3 install -r requirements.txt || handle_error "Failed to install Python dependencies"

echo -e "${BLUE}Installing frontend dependencies...${NC}"
cd frontend
npm install || handle_error "Failed to install frontend dependencies"
cd ..

# Export environment variables if they exist in a .env file
if [ -f .env ]; then
    echo -e "${BLUE}Loading environment variables...${NC}"
    export $(cat .env | xargs)
fi

# Start the backend server in the background
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start the frontend
echo -e "${GREEN}Starting frontend development server...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Function to cleanup processes on script termination
cleanup() {
    echo -e "${BLUE}\nShutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Register the cleanup function for script termination
trap cleanup SIGINT SIGTERM

# Keep the script running and show logs
echo -e "${GREEN}Services are running!${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 
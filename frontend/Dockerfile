FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package.json ./package.json
RUN npm install

# Set environment variables
ENV NODE_ENV=development
ENV PATH /app/node_modules/.bin:$PATH

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application in development mode
CMD ["npm", "start"] 
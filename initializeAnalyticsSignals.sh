#!/bin/bash

echo "Stopping backend container..."
docker-compose -f docker-compose.yml down --timeout 60 osai_backend

echo "Building backend container..."
docker-compose -f docker-compose.yml build osai_backend

echo "Installing backend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d osai_backend

echo "Backend container installed successfully!"

#

# echo "Stopping frontend container..."
# docker-compose -f docker-compose.yml down --timeout 60 osai_frontend

# echo "Building frontend container..."
# docker-compose -f docker-compose.yml build osai_frontend

# echo "Installing frontend container..."
# docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d osai_frontend

# echo "Frontend container installed successfully!"

# echo "Listing all running containers..."
# docker ps

# echo "Showing backend logs..."
# docker logs -f osai_backend
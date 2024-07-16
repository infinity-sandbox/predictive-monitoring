#!/bin/bash

echo "Stopping backend container..."
docker-compose -f docker-compose.yml down --timeout 60 backend1

echo "Building backend container..."
docker-compose -f docker-compose.yml build backend1

echo "Installing backend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d backend1

echo "Backend container installed successfully!"

#

echo "Stopping frontend container..."
docker-compose -f docker-compose.yml down --timeout 60 frontend1

echo "Building frontend container..."
docker-compose -f docker-compose.yml build frontend1

echo "Installing frontend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d frontend1

echo "Frontend container installed successfully!"

echo "Listing all running containers..."
docker ps

echo "Showing backend logs..."
docker logs -f backend1
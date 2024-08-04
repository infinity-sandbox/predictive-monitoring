#!/bin/bash

echo "Stopping backend container..."
docker-compose -f docker-compose.yml down --timeout 60 osai_backend

echo "Building backend container..."
docker-compose -f docker-compose.yml build osai_backend

echo "Installing backend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d osai_backend

echo "Backend container installed successfully!"

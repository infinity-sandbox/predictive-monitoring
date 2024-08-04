#!/bin/bash

echo "Stopping frontend container..."
docker-compose -f docker-compose.yml down --timeout 60 osai_frontend

echo "Building frontend container..."
docker-compose -f docker-compose.yml build osai_frontend

echo "Installing frontend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d osai_frontend

echo "Frontend container installed successfully!"

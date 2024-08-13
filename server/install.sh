#!/bin/bash

echo "Stopping backend container..."
docker-compose -f docker-compose.yml down --timeout 60 backend_applicare

echo "Building backend container..."
docker-compose -f docker-compose.yml build backend_applicare

echo "Installing backend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d backend_applicare

echo "Backend container installed successfully!"

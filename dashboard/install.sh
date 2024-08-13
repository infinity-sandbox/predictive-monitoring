#!/bin/bash

echo "Stopping frontend container..."
docker-compose -f docker-compose.yml down --timeout 60 frontend_applicare

echo "Building frontend container..."
docker-compose -f docker-compose.yml build frontend_applicare

echo "Installing frontend container..."
docker-compose -f docker-compose.yml up --remove-orphans --force-recreate -d frontend_applicare

echo "Frontend container installed successfully!"

#!/bin/bash

cd server
chmod +x install.sh
source install.sh

cd ..

cd dashboard
chmod +x install.sh
source install.sh

cd ..

echo "Listing all running containers..."
docker ps

echo "Showing backend logs..."
docker logs -f backend_applicare

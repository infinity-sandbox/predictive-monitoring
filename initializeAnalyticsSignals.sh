#!/bin/bash

chmod +x setupEnvironment.sh
source setupEnvironment.sh
# ------------------------------------------------------------
cd server
chmod +x install_be.sh
source install_be.sh

cd ..

cd dashboard
chmod +x install_fe.sh
source install_fe.sh

cd ..
# ------------------------------------------------------------
echo "Listing all running containers..."
docker ps

echo "Showing backend logs..."
docker logs -f osai_backend

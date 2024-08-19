#!/bin/bash

echo "Copying the folder to the Documents folder..."
[ -f ~/Documents/predictive-monitoring.zip ] && rm ~/Documents/predictive-monitoring.zip
[ -d ~/Documents/predictive-monitoring ] && rm -rf ~/Documents/predictive-monitoring
cp -r . ~/Documents/predictive-monitoring

echo 'Going inside ~/Documents/predictive-monitoring...'
cd ~/Documents/predictive-monitoring

echo "Deleting environments..."
rm -rf dashboard/node_modules
rm -rf server/venv

echo "Deleting unwanted files..."
rm -rf server/logs/logs.log
rm -rf test_folder
rm -rf .git/
rm -rf .gitignore

echo "Deleting unwanted lines..."
sed -i '' 's/MONGO.*//g' server/docker-compose.yml

echo "Reseting environments..."
chmod +x setupEnvironment.sh
source setupEnvironment.sh

echo 'Zipping the folder...'
PARENT_DIR=$(dirname "$PWD")
FOLDER_NAME=$(basename "$PWD")

zip -r "${PARENT_DIR}/${FOLDER_NAME}.zip" .

echo "[-] Folder ${FOLDER_NAME} has been zipped as ${FOLDER_NAME}.zip in ${PARENT_DIR}"
echo "[-] Cleanining Completed!"
echo "[+] Send the code to the client!"


#!/bin/bash

echo "=============================="
echo "  Setup Backend Environments  "
echo "=============================="

ENV_FILE="./server/.env"

# Create the .env directory if it doesn't exist
mkdir -p "$(dirname "$ENV_FILE")"

# Write content to the .env file
cat <<EOF > "$ENV_FILE"
MYSQL_DB_HOST=""
MYSQL_DB_PORT=""
MYSQL_DB_USER=""
MYSQL_DB_PASSWORD=""
MYSQL_DB=""
FRONTEND_API_URL="http://0.0.0.0:3000"
BACKEND_API_URL="http://0.0.0.0:8000"
JWT_SECRET_KEY="d8d8dd321e08dd2e2dd6fdf2f07e2ff3"
JWT_REFRESH_SECRET_KEY="47eacd8a01ee705177f1678d675884cf"
MONGO_CONNECTION_STRING="mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.2.10"
MY_EMAIL_PASSWORD=""
MY_EMAIL="abelmgetnet@gmail.com"
EMAIL_APP_PASSWORD="hqlo pnzb udno usqq"
OPENAI_API_KEY=""
MODEL="gpt-3.5-turbo"
EOF

echo "Environment variables written to $ENV_FILE"

echo "=============================="
echo " Setup Frontend Environments  "
echo "=============================="

ENV_FILE_DEV="./dashboard/.env"

# Create the .env directory if it doesn't exist
mkdir -p "$(dirname "$ENV_FILE_DEV")"

# Write content to the .env file
cat <<EOF > "$ENV_FILE_DEV"
REACT_APP_BACKEND_API_URL="http://0.0.0.0:8000"
REACT_APP_FRONTEND_API_URL="http://0.0.0.0:3000"
EOF

echo "Environment variables written to $ENV_FILE_DEV"

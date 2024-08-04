#!/bin/bash

echo "=============================="
echo "  Setup Backend Environments  "
echo "=============================="

ENV_FILE="./server/.env"

# Create the .env directory if it doesn't exist
mkdir -p "$(dirname "$ENV_FILE")"

# Write content to the .env file
cat <<EOF > "$ENV_FILE"
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY_ID=""
OPENAI_API_KEY=""
SLACK_BOT_TOKEN=""
SLACK_CLIENT_ID=""
SLACK_CLIENT_SECRET=""
SLACK_SIGNING_SECRET=""
SLACK_USER_TOKEN=""
SPOTIFY_CLIENT_ID=""
SPOTIFY_CLIENT_SECRET=""
SPOTIFY_REDIRECT_URI=""
WEAVIATE_API_KEY=""
WEAVIATE_MODEL="gpt-4"
WEAVIATE_URL=""
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
VITE_API_BACKEND_URL="https://dev-apply-cms.10academy.org"
VITE_API_CHATBOT_BACKEND_URL="https://dev-nana.10academy.org"
EOF

echo "Environment variables written to $ENV_FILE_DEV"

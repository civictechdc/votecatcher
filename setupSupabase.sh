#! /bin/bash

# Exit on error
set -e

# Prompt for project reference
read -p "Enter your Supabase project id (found in the dashboard URL): " PROJECT_REF

# Check if project reference was provided
if [ -z "$PROJECT_REF" ]; then
  echo "Error: Project reference cannot be empty." >&2
  exit 1
fi

read -sp "Enter your Supabase database password: " SUPABASE_DB_PASSWORD
echo ""

echo "Starting migrations..."

# Link the project
supabase link --project-ref $PROJECT_REF -p $SUPABASE_DB_PASSWORD
SUPABASE_DB_PASSWORD=$SUPABASE_DB_PASSWORD supabase db push --yes

echo ""
echo "Deploying functions..."
supabase functions deploy --project-ref $PROJECT_REF --use-api

unset SUPABASE_DB_PASSWORD

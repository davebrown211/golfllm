#!/bin/bash

# Golf Directory Clean Deploy Script
# This script ensures a clean build with all caches cleared

set -e  # Exit on any error

echo "🚀 Starting clean deployment..."

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend/golf-directory"

echo "📁 Current directory: $(pwd)"

# Clear all caches
echo "🧹 Clearing caches..."
rm -rf .next
rm -rf node_modules/.cache
rm -rf dist
rm -rf build

# Install dependencies fresh
echo "📦 Installing dependencies..."
npm ci

# Run clean build
echo "🔨 Building application..."
npm run build

echo "✅ Clean build completed successfully!"
echo "📋 Ready to deploy with: npm start"
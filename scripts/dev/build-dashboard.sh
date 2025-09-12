#!/bin/bash

# Build the React dashboard for production

echo "Building React dashboard for production..."
cd dashboard
npm install
npm run build
echo "Dashboard build complete."
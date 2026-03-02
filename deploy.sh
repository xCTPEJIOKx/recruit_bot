#!/bin/bash
# Deploy to GitHub and Render

set -e

echo "============================================================"
echo "    Deployment Script - Recruitment System"
echo "============================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Copy .env.example to .env and fill in your credentials"
    exit 1
fi

# Remove sensitive files from git
echo "🔒 Removing sensitive files from git cache..."
git rm --cached .env 2>/dev/null || true
git rm --cached data/*.db 2>/dev/null || true

# Clean up
echo "🧹 Cleaning up..."
rm -rf __pycache__ */__pycache__ */*/__pycache__
rm -f cloudflared
rm -rf .pytest_cache .coverage htmlcov

# Git add and commit
echo "📦 Staging changes..."
git add -A

echo "💾 Committing changes..."
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "============================================================"
echo "    ✅ Deployment Complete!"
echo "============================================================"
echo ""
echo "📊 Next Steps:"
echo ""
echo "1. Go to https://render.com"
echo "2. Connect your repository: xCTPEJIOKx/recruit_bot"
echo "3. Add environment variables from .env"
echo "4. Deploy!"
echo ""
echo "📱 After deployment:"
echo "   - Update Telegram Bot Menu Button URL"
echo "   - Test Web App: https://your-app.onrender.com/static/index.html"
echo ""
echo "📖 Full instructions: docs/DEPLOY_RENDER.md"
echo "============================================================"

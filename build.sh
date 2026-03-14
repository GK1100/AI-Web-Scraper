#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Install Chromium to the exact path Render expects
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
playwright install chromium --with-deps

# GitHub Star Crawler

## Overview
Automated system to crawl and store GitHub repository data using GitHub Actions.

## Features
- Crawls 100,000+ repos with pagination
- Rate-limit handling with automatic retries
- PostgreSQL storage with upsert logic
- Daily scheduled runs via GitHub Actions
- CSV export as artifacts

## Architecture
- **Data Source:** GitHub GraphQL API
- **Database:** PostgreSQL (service container in Actions)
- **Orchestration:** GitHub Actions (daily cron + manual trigger)
- **Export:** CSV artifacts stored in Actions

## Setup
1. Add `GH_TOKEN` secret (GitHub PAT with repo read access)
2. Workflow triggers automatically on push/schedule
3. Download results from Actions artifacts
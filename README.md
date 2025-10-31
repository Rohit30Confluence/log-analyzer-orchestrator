# Log Analyzer Orchestrator

> Deployment, monitoring, and DNS automation layer for the Log Analyzer Attack Detection platform — enabling streamlined CI/CD, environment sync, and production stability.

## 🧠 Overview
The **Log Analyzer Orchestrator** automates infrastructure operations, manages service reliability, and monitors runtime stability for the main [Log Analyzer Attack Detection](https://github.com/Rohit30Confluence/log-analyzer-attack-detection) repository.

This system ensures:
- Automated CI/CD deploys across environments  
- Smart DNS mapping for service continuity  
- Continuous health checks and uptime logging  
- Deployment issue resolution and rollback triggers  

## 🏗️ Architecture
- **FastAPI-based microservice**
- **Render-compatible CI/CD YAML**
- **Redis-backed event store (optional)**
- **DNS resolver abstraction** for multiple providers
- **Automated health monitoring** integrated with status API

## 🚀 Usage
```bash
pip install -r requirements.txt
python orchestrator/main.py

# Trustworthy ML Model Registry

A full-stack web application for managing and tracking machine learning artifacts (models, datasets, code) with trust scoring, lineage tracking, and integration with HuggingFace Hub.

**Course:** ECE 461 - Software Engineering (Fall 2025)  
**Phase:** 2 - Trustworthy Model Registry

## 🚀 Live Demo

- **API Endpoint:** https://xi43tvk341.execute-api.us-east-1.amazonaws.com
- **Web UI:** https://swe-proj-phase2-frontend-nl3x1rovn-same-s-projects.vercel.app

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Testing](#testing)
- [Team](#team)

## ✨ Features

### Core Functionality

- **Artifact Management** - Create, read, update, and delete ML artifacts (models, datasets, code)
- **HuggingFace Integration** - Ingest models directly from HuggingFace Hub with automatic metadata extraction
- **Trust Scoring** - Calculate trust scores based on multiple factors:
  - Dataset and code availability
  - Dataset quality metrics
  - Performance claims validation
- **Model Rating System** - Community ratings with upvote/downvote functionality
- **Lineage Tracking** - Track relationships between models, their training datasets, and base models
- **Search & Query** - Filter artifacts by name, type, ID, and other attributes

### Technical Features

- Serverless architecture with AWS Lambda
- DynamoDB for scalable NoSQL storage
- RESTful API following OpenAPI 3.0 specification
- CORS-enabled for cross-origin requests
- Consistent reads for data accuracy

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Frontend      │────▶│   API Gateway   │────▶│   Lambda        │
│   (Vercel)      │     │   (HTTP API)    │     │   (Python 3.12) │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌─────────────────┐              │
                        │                 │              │
                        │   DynamoDB      │◀─────────────┘
                        │   (NoSQL)       │
                        │                 │              │
                        └─────────────────┘              │
                                                         │
                        ┌─────────────────┐              │
                        │                 │              │
                        │   HuggingFace   │◀─────────────┘
                        │   Hub API       │
                        │                 │
                        └─────────────────┘
```

### Tech Stack

- **Backend:** Python 3.12, AWS Lambda, Boto3
- **Database:** Amazon DynamoDB (single-table design)
- **Infrastructure:** AWS SAM/CloudFormation
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Hosting:** AWS API Gateway (backend), Vercel (frontend)
- **External APIs:** HuggingFace Hub

## 📁 Project Structure

```
swe-proj-phase2/
├── backend/
│   ├── app.py              # Main Lambda handler with all API logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── app.js              # Frontend application logic
│   ├── api.js              # API client functions
│   └── styles.css          # Styling
├── infrastructure/
│   ├── template.yaml       # SAM/CloudFormation template
│   └── samconfig.toml      # SAM deployment configuration
├── ece461_fall_2025_openapi_spec.yaml  # API specification
├── test_autograder_endpoints.sh        # API test script
└── README.md
```

## 🔌 API Endpoints

### Health Check

| Method | Endpoint             | Description              |
| ------ | -------------------- | ------------------------ |
| GET    | `/health`            | Heartbeat check          |
| GET    | `/health/components` | Component health details |

### Artifacts

| Method | Endpoint         | Description           |
| ------ | ---------------- | --------------------- |
| POST   | `/artifacts`     | Query/list artifacts  |
| POST   | `/artifact`      | Create a new artifact |
| GET    | `/artifact/{id}` | Get artifact by ID    |
| PUT    | `/artifact/{id}` | Update artifact       |
| DELETE | `/artifact/{id}` | Delete artifact       |

### HuggingFace Integration

| Method | Endpoint           | Description                     |
| ------ | ------------------ | ------------------------------- |
| POST   | `/ingestHFModel`   | Ingest model from HuggingFace   |
| POST   | `/ingestHFDataset` | Ingest dataset from HuggingFace |
| POST   | `/ingestGHCode`    | Ingest code from GitHub         |

### Scoring & Rating

| Method | Endpoint                 | Description          |
| ------ | ------------------------ | -------------------- |
| GET    | `/artifact/{id}/scores`  | Get trust scores     |
| POST   | `/artifact/{id}/rate`    | Rate an artifact     |
| GET    | `/artifact/{id}/ratings` | Get artifact ratings |

### Lineage

| Method | Endpoint                 | Description                |
| ------ | ------------------------ | -------------------------- |
| GET    | `/artifact/{id}/lineage` | Get artifact lineage graph |

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- AWS CLI configured with credentials
- AWS SAM CLI
- Node.js (for frontend development)

### Local Development

1. **Clone the repository:**

   ```bash
   git clone https://github.com/samekiflu/swe-proj-phase2.git
   cd swe-proj-phase2
   ```

2. **Install backend dependencies:**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   ```bash
   export DYNAMODB_TABLE_NAME=TrustModelRegistry
   ```

4. **Run frontend locally:**
   ```bash
   cd frontend
   # Open index.html in a browser or use a local server
   python -m http.server 8000
   ```

## 📦 Deployment

### Backend (AWS SAM)

1. **Build the SAM application:**

   ```bash
   cd infrastructure
   sam build
   ```

2. **Deploy to AWS:**

   ```bash
   sam deploy --guided
   ```

   Or with existing configuration:

   ```bash
   sam deploy
   ```

### Frontend (Vercel)

1. **Install Vercel CLI:**

   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel --prod
   ```

## 🧪 Testing

### Run API Tests

```bash
./test_autograder_endpoints.sh
```

### Manual Testing

Use the provided OpenAPI specification with tools like:

- Postman
- curl
- httpie

Example API call:

```bash
curl -X GET "https://xi43tvk341.execute-api.us-east-1.amazonaws.com/health"
```

## 🔐 Security Features

- HTTPS-only API endpoints
- AWS IAM-based authentication for backend services
- Input validation on all endpoints
- CORS configuration for controlled access
- DynamoDB encryption at rest

## 📊 Trust Score Calculation

The trust score is calculated based on three components:

| Component                | Weight | Description                            |
| ------------------------ | ------ | -------------------------------------- |
| `dataset_and_code_score` | 33%    | Availability of training data and code |
| `dataset_quality`        | 33%    | Quality metrics of associated datasets |
| `performance_claims`     | 33%    | Validation of model performance claims |

Each component is scored 0-100, and the overall trust score is the weighted average.


## 📄 License

This project is developed for educational purposes as part of ECE 461 at Purdue University.

## 🙏 Acknowledgments

- Prof. Steve France - Course Instructor
- Prof. James Davis - Course Instructor
- AWS - Cloud Infrastructure

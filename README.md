Trustworthy Model Registry – Phase 2
ECE 461 – Software Engineering

This project implements a serverless Model Registry API using AWS Lambda, DynamoDB, and API Gateway.
The backend is written in Python, deployed using AWS SAM, and supports all required API endpoints defined for Phase 2.

✅ Features Implemented

1. Health Endpoints (No Auth Required)

GET /health – Basic system status

GET /health/components – Component-level diagnostic information

2. Authentication

PUT /authenticate

Accepts a username and password

Returns a bearer token (bearer valid-token) on success

Authentication is required for all endpoints except:

/health

/health/components

/tracks

/authenticate

3. Tracks Endpoint

GET /tracks
Returns the predefined list of planned tracks.

4. Artifact Management

Supports three artifact types:
model, dataset, and code.

Create
POST /artifact/{artifact_type}

Retrieve
GET /artifacts/{artifact_type}/{id}

Update
PUT /artifacts/{artifact_type}/{id}

Delete
DELETE /artifact/{artifact_type}/{id}

Each stored artifact includes:

ID

Name

URL

Generated download URL

License info

Lineage

Cost metadata

Creation / update timestamps

5. Additional Functionality
   Search by Name
   GET /artifact/byName/{name}

Search by Regex
POST /artifact/byRegEx

List multiple artifacts
POST /artifacts

Model Rating
GET /artifact/model/{id}/rate

Returns the latest rating or generates a new one if missing.

Cost Calculation
GET /artifact/{artifact_type}/{id}/cost
GET /artifact/{artifact_type}/{id}/cost?dependency=true

Lineage Retrieval
GET /artifact/model/{id}/lineage

License Compatibility
POST /artifact/model/{id}/license-check

Audit History
GET /artifact/{artifact_type}/{id}/audit

Reset Registry
DELETE /reset

Clears all metadata and ratings.

✅ Deployment Instructions (AWS SAM)
Build
cd infrastructure
sam build

Deploy
sam deploy --guided

This creates:

DynamoDB Table

Lambda Function

HTTP API Gateway

The base URL is printed in the SAM output as:

ApiUrl: https://xxxx.execute-api.us-east-1.amazonaws.com

🔧 Project Structure
swe-proj-phase2/
│
├── backend/
│ ├── app.py
│ └── requirements.txt
│
├── infrastructure/
│ ├── template.yaml
│ └── samconfig.toml
│
├── README.md
└── .gitignore

🧪 Testing

All endpoints were tested using:

curl

AWS API Gateway console

Tests included:

Authentication

Create / Read / Update / Delete

Rating

Cost calculation

Lineage

Regex and name searches

Full registry reset

All endpoints returned valid responses after deployment.

# AnyCart — Agentic AI Order Management Platform

AnyCart is a cloud-native, agentic AI e-commerce application that uses **LangGraph** and **Amazon Bedrock** to orchestrate conversational product recommendations, order placement, and order tracking.

The project demonstrates how an LLM-powered agent can securely interact with serverless tools and backend services while maintaining clear boundaries between AI reasoning, application logic, and cloud infrastructure.

## Overview

AnyCart provides a conversational shopping experience where users can:

- Discover and receive product recommendations
- Place orders using natural language
- Track existing orders using an order ID
- Interact with specialized backend tools through a LangGraph orchestrator

The application uses **Streamlit** as the frontend, **LangGraph** for workflow orchestration, **Amazon Bedrock** for model inference, **AWS Lambda** for serverless tools, and **Amazon DynamoDB** for order persistence.

## Architecture

```text
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Streamlit UI     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Main AWS Lambda    │
                         │   LangGraph Agent   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Orchestrator    │
                         │ Intent + Parameters │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ Recommendation │ │  Place Order   │ │  Track Order   │
        │     Agent      │ │     Agent      │ │     Agent      │
        └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
                │                  │                  │
                ▼                  ▼                  ▼
        recommend-product     place-orders       order-status
            Lambda               Lambda             Lambda
                │                  │                  │
                ▼                  └────────┬─────────┘
        Amazon Bedrock                     │
        Knowledge Base                     ▼
                                      DynamoDB
```

## Core Capabilities

### Intelligent Product Recommendations

The recommendation workflow uses Amazon Bedrock and retrieval capabilities to provide product information based on natural-language requests.

### Conversational Order Placement

Users can request products conversationally. The LangGraph orchestrator identifies the request, extracts required parameters, and routes the action to the appropriate AWS Lambda tool.

### Order Tracking

Users can provide an order ID to retrieve the current order status and quantity stored in Amazon DynamoDB.

### Agent Orchestration

LangGraph manages application state and routes requests between specialized workflows for recommendation, ordering, and tracking.

## Technology Stack

| Layer | Technologies |
|---|---|
| Agent Orchestration | LangGraph, LangChain |
| Generative AI | Amazon Bedrock, Amazon Nova Lite |
| Retrieval | Amazon Bedrock Knowledge Bases |
| Compute | AWS Lambda |
| Database | Amazon DynamoDB |
| Container Registry | Amazon ECR |
| Cloud SDK | Boto3 |
| Frontend | Streamlit |
| Containerization | Docker |
| Language | Python |
| Dependency Management | uv |
| Access Control | AWS IAM |

## Project Structure

```text
order_management/
├── agent/
│   ├── __init__.py
│   └── graph.py
│
├── assets/
│   └── images/
│
├── deployment/
│   └── Dockerfile
│
├── tests/
│
├── ui/
│   ├── __init__.py
│   ├── catalog.py
│   └── streamlit_app.py
│
├── .gitignore
├── .python-version
├── main.py
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

## Request Flow

A typical request follows this workflow:

```text
User Request
     │
     ▼
Streamlit
     │
     ▼
AWS Lambda
     │
     ▼
LangGraph Orchestrator
     │
     ├── Product Recommendation
     │
     ├── Order Placement
     │
     └── Order Tracking
     │
     ▼
AWS Services / Tools
     │
     ▼
Response returned to user
```

The orchestrator determines the user's intent and extracts relevant information such as product identifiers, quantity, or order ID before routing the request to the appropriate tool.

## Local Development

### Prerequisites

The project requires:

- Python 3.12
- uv
- Docker
- AWS CLI
- Valid AWS credentials with access to the required services

### Install Dependencies

```bash
uv sync
```

### Configure AWS

Use an AWS CLI profile or another supported AWS credential provider.

Example:

```bash
export AWS_PROFILE=<your-profile>
export AWS_REGION=us-east-2
```

> AWS credentials should never be committed to the repository.

Verify authentication:

```bash
aws sts get-caller-identity
```

### Run the Application

From the project root:

```bash
uv run streamlit run ui/streamlit_app.py
```

The application will be available at:

```text
http://localhost:8501
```

## Container Deployment

The LangGraph application is packaged as an AWS Lambda container image.

Build the image from the project root:

```bash
docker build \
  --platform linux/amd64 \
  --provenance=false \
  -f deployment/Dockerfile \
  -t order-management .
```

The Lambda container entry point is:

```text
agent.graph.lambda_handler
```

The image can then be published to Amazon ECR and deployed to AWS Lambda.

## Security Considerations

Agentic applications introduce security boundaries beyond those found in traditional web applications. This project provides a practical environment for evaluating risks across the **user → LLM → agent → tool → cloud service** execution chain.

Key security considerations include:

- Prompt injection and malicious instructions
- Unauthorized or excessive tool invocation
- Least-privilege IAM permissions
- LLM-to-tool trust boundaries
- Input validation for Lambda functions
- Authentication and authorization of order operations
- IDOR risks associated with order identifiers
- Sensitive-data exposure through prompts or responses
- Retrieval and knowledge-base trust boundaries
- Dependency and container vulnerabilities
- Secret and credential management
- Logging and auditability of agent actions

Credentials and local environment secrets are excluded from source control.

## Security Roadmap

Future security enhancements include:

- SAST integration
- Software Composition Analysis (SCA)
- Automated secret scanning
- Container vulnerability scanning
- CI/CD security gates
- Prompt-injection and adversarial testing
- Tool-level authorization controls
- API authentication and authorization
- Structured security logging
- Automated security tests
- SBOM generation

## Key Engineering Concepts Demonstrated

This project demonstrates practical experience with:

- Agentic AI application architecture
- LangGraph state and workflow orchestration
- LLM tool calling
- Retrieval-Augmented Generation (RAG)
- Serverless application architecture
- AWS IAM and service integration
- Lambda container deployment
- DynamoDB-backed application workflows
- Docker and Amazon ECR
- AI application threat modeling
- Secure agent-to-tool design

## Disclaimer

This project is intended for educational, engineering, and security research purposes. It is not a production e-commerce platform and should not be used to process real customer, payment, or sensitive personal information without additional production security controls.

## Author

**Deborah Quaye**

Application Security | AI Security | Cloud Security | Agentic AI
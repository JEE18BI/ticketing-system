# Customer Support Ticketing System

A containerized Customer Support Ticketing System built with Flask, MySQL, Docker, Docker Compose, and Kubernetes. The system allows users to create support tickets, assign them to support agents, close tickets, view notifications, and generate reporting statistics.

## Architecture

The system is organized into multiple independent services:

| Service | Description | Internal Port |
|---|---|---|
| Frontend | Static dashboard served by Nginx | 80 |
| Ticket Service | Creates, updates, deletes, and lists tickets | 5000 |
| Support Service | Handles ticket assignment, closing, and responses | 5001 |
| Notification Service | Stores and returns ticket event notifications | 5002 |
| Reporting Service | Generates ticket statistics and reports | 5003 |
| MySQL Database | Stores ticket data | 3306 |

Services communicate with each other through HTTP APIs using Docker/Kubernetes service names.

## Technologies Used

- Python Flask
- MySQL 8
- Nginx
- Docker
- Docker Compose
- Kubernetes
- Minikube

## Project Structure

```text
ticketing-system/
|-- docker-compose.yml
|-- docker-compose.dev.yml
|-- docker-compose.test.yml
|-- docker-compose.prod.yml
|-- frontend/
|   |-- Dockerfile
|   |-- index.html
|   |-- config.js
|   |-- config.dev.js
|   |-- config.test.js
|   `-- config.prod.js
|-- ticket-service/
|   |-- Dockerfile
|   |-- app.py
|   `-- requirements.txt
|-- support-service/
|   |-- Dockerfile
|   |-- app.py
|   `-- requirements.txt
|-- notification-service/
|   |-- Dockerfile
|   |-- app.py
|   `-- requirements.txt
|-- reporting-service/
|   |-- Dockerfile
|   |-- app.py
|   `-- requirements.txt
`-- k8s/
    |-- db.yaml
    |-- frontend.yml
    |-- ticket-service.yaml
    |-- support-service.yaml
    |-- notification-service.yaml
    `-- reporting-service.yaml

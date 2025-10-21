Māori Story Fill - Backend Service

1. Overview

This repository contains the backend service for the Māori Story Fill application. It is a Django-based REST API that provides story templates, manages user creations, and handles all core business logic.

The service is designed to be containerized with Docker and deployed on a Kubernetes cluster.

2. Tech Stack

Framework: Django

API: Django REST Framework

Database: PostgreSQL

Production Server: Gunicorn

CI/CD: GitHub Actions

Containerization: Docker

3. Local Development Setup

Prerequisites

Python 3.13+

Pip for dependency management

Docker and Docker Compose (for running a local PostgreSQL instance)

Step-by-Step Guide

Clone the Repository

git clone <your-repository-url>
cd maori-story-fill/backend


Install Dependencies
It's recommended to use a virtual environment.

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt


Configure Environment Variables
Create a .env file in the backend/ directory by copying the example template.

cp .env.example .env


Now, edit the .env file and set your local database credentials and a new SECRET_KEY.

Start the Database
If you are using Docker for a local database, ensure your PostgreSQL container is running.

Run Database Migrations
This will create the necessary tables in your database.

python manage.py migrate


Run the Development Server

python manage.py runserver

#Can trigger pipeline by modify files in folder backend/ .
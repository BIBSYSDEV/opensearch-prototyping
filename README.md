# README

This repo contains a simple example of how to use the `opensearch-py` library to interact with an Opensearch instance.
This is intended to be used for prototyping and testing OpenSearch indexes and queries.

It uses a Docker container to run an Opensearch instance and a Python script to interact with it.

## Usage

```bash
# Run Opensearch instance with Docker
docker-compose up -d

# Set up Python dependencies
python -m pip install --upgrade pip
pip install pip-tools
pip-compile requirements.in
python -m pip install -r requirements.txt

# Run example script
python ./main.py

# Run linting/formatting manually
black .
flake8 .
mypy .
```

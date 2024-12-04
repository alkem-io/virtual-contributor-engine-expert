# Use an official Python runtime as a parent image
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bullseye AS builder

RUN apt-get update 
RUN apt-get install git -y

# Set the working directory in the container to /app
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the current directory contents into the container at /app
COPY . /app

# Use Poetry to install dependencies
RUN poetry config virtualenvs.create true && poetry install --no-interaction --no-ansi

# Run guidance_engine.py when the container launches
CMD ["poetry", "run", "python", "main.py"]

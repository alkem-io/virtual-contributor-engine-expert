# Use an official Python runtime as a parent image
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bullseye as builder

# Set the working directory in the container to /app
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the current directory contents into the container at /app
COPY . /app

# Use Poetry to install dependencies
RUN poetry config virtualenvs.create true && poetry install --no-interaction --no-ansi

# Start a new, final stage
# FROM python:${PYTHON_VERSION}-slim-bullseye

# WORKDIR /app

# # Install git and Poetry in the final stage
# RUN apt update && apt install -y git && pip install poetry

# # Copy the compiled app, Hugo executable, Go, and the virtual environment from the previous stage
# COPY --from=builder /app /app
# # COPY --from=builder /usr/local/hugo /usr/local/hugo
# # COPY --from=builder /usr/local/go /usr/local/go
# COPY --from=builder /root/.cache/pypoetry/virtualenvs /root/.cache/pypoetry/virtualenvs

# Add Hugo and Go to the PATH
# ENV PATH="/usr/local/hugo:/usr/local/go/bin:${PATH}"

# Run guidance_engine.py when the container launches
CMD ["poetry", "run", "python", "virtual_contributor.py"]

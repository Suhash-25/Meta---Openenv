# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the environment and inference files into the container
COPY . .

# Set environment variables (Placeholders - the evaluator will inject real ones)
ENV API_BASE_URL="http://localhost:8000/v1"
ENV MODEL_NAME="baseline-model"
ENV HF_TOKEN="dummy_token"

CMD ["python", "inference.py"]
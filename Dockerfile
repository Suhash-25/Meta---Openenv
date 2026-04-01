# 1. Use a standard Python base image
FROM python:3.10-slim

# 2. CRITICAL FOR HUGGING FACE: Create a non-root user (UID 1000)
RUN useradd -m -u 1000 user
USER user

# 3. Explicitly set the PATH so the user can find pip-installed tools
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 4. Set the working directory
WORKDIR $HOME/app

# 5. Copy files and ensure the new 'user' owns them
COPY --chown=user . $HOME/app

# 6. Install dependencies AS the user (Adding fastapi and uvicorn)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

# 7. Set required environment variables
ENV API_BASE_URL="http://localhost:8000/v1"
ENV MODEL_NAME="baseline-model"
ENV HF_TOKEN="dummy_token"

# 8. The Toggle: Run Streamlit if APP_MODE is set, otherwise run our custom FastAPI server
CMD if [ "$APP_MODE" = "streamlit" ]; then \
        echo "🚀 Starting Streamlit Dashboard..."; \
        streamlit run app.py --server.port 7860 --server.address 0.0.0.0; \
    else \
        echo "🤖 Starting Custom OpenEnv Evaluation Server..."; \
        uvicorn server.app:app --host 0.0.0.0 --port 7860; \
    fi
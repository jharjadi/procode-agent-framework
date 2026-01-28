FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire external_agents directory structure
COPY . /app/external_agents/insurance_agent/
COPY ../shared /app/external_agents/shared/

# Set Python path to include parent directories
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 9997

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:9997/health', timeout=5.0)" || exit 1

# Run the agent
CMD ["python", "-m", "external_agents.insurance_agent"]

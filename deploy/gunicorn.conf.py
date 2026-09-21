# Gunicorn Production Configuration for ASTRA ML Backend
import os

port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"
workers = 1  # Exactly 1 warm ML process worker per instance to prevent model duplication in RAM
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120  # Allow lifespan model loading & warmup
keepalive = 65  # Maintain persistent connections with Nginx reverse proxy

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Environment Defaults
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("ASTRA_DEVICE", "cpu")

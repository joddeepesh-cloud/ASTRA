# Gunicorn Production Configuration for ASTRA ML Backend
import os

bind = "0.0.0.0:8000"
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

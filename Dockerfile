FROM python:3.11-slim

WORKDIR /app

# Install requests dependency
RUN pip install --no-cache-dir requests

# Copy source code files
COPY enchilada.py config.py cs_helpers.py /app/

# Set unbuffered python entrypoint
ENTRYPOINT ["python", "-u", "enchilada.py"]

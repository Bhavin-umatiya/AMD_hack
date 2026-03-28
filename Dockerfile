# Use Python 3.12 slim for smaller image size
FROM python:3.12-slim

# Install system dependencies: Iverilog and Yosys for FPGA workflows
RUN apt-get update && apt-get install -y --no-install-recommends \
    iverilog \
    yosys \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and NPM for NetlistSVG (RTL Visualization)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g netlistsvg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Create temporary directory for simulations
RUN mkdir -p /app/sim_temp && chmod 777 /app/sim_temp

# Expose the API port
EXPOSE 5000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5000
ENV PYTHONIOENCODING=utf-8

# Start the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "2", "app:app"]

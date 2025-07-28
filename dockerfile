# Dockerfile

# 1. Base Image: Use a specific, slim Python image and lock the platform to amd64.
FROM --platform=linux/amd64 python:3.9-slim

# 2. Set the working directory inside the container.
WORKDIR /app

# 3. Copy and install Python dependencies. This is done before copying the main
#    code to leverage Docker's layer caching for faster rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Download NLTK data during the build. This is the crucial step for offline
#    operation. The data will be baked into the image layer.
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

# 5. Copy your application source code into the container.
COPY src/ .

# 6. Create mount points for the I/O directories.
RUN mkdir -p /app/input /app/output

# 7. Specify the command to run when the container starts. This executes the script.
CMD ["python", "main.py"]
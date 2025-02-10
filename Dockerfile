FROM python:3.10-slim

# Set the working directory
WORKDIR /app


COPY . /app

# Install required dependencies (if any)
RUN pip install -r requirements.txt

# Expose port 8000 for the application
EXPOSE 8000

# Run the application
CMD ["python3", "app.py"]

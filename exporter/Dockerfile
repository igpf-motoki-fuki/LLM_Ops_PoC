FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY claude_code_exporter.py .

ENV PYTHONUNBUFFERED=1

EXPOSE 9101

CMD ["python", "claude_code_exporter.py"]

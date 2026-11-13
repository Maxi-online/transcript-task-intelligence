FROM python:3.10-slim

WORKDIR /app
ENV PYTHONPATH="/app"

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY src src/
COPY main.py .

# Запускаем приложение
CMD ["python", "main.py"]

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/user_service/ ./services/user_service/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "services.user_service.main:app", "--host", "0.0.0.0", "--port", "8001"]

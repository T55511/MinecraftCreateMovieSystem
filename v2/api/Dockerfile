# FROM python:3.12-slim

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8010
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]


FROM python:3.12-slim

WORKDIR /app/v2

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8010
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]

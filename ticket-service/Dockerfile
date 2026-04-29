FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install flask mysql-connector-python flask-cors

CMD ["python", "app.py"]
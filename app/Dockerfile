FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt /app

RUN pip3 install -r requirements.txt

COPY . /app

# ENTRYPOINT ["python3"]
CMD ["python3", "app.py"]
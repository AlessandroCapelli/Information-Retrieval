FROM python:3.7.3-alpine

COPY . /app

WORKDIR /app

RUN pip install -U pip

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]
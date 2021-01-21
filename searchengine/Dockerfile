FROM python:3.7.3

COPY . /app

WORKDIR /app

RUN pip install -U pip

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["search_engine.py"]
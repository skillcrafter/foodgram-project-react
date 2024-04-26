FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi:application"]

FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py makemigrations

RUN python manage.py migrate

# RUN python manage.py load_data_tag

# RUN python manage.py recipes/management/commands/load_data_tag.py

# sudo docker compose exec backend python manage.py load_data_ingrediend


CMD ["gunicorn", "--bind", "0.0.0.0:9000", "foodgram.wsgi:application"]

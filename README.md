# Продуктовый помощник. Включает в себя функции создания рецептов, сохранения 
# их в избранное, добавления в корзину покупок, которую можно скачать 
### в формате txt. Также есть возможность подписки на других авторов.
### Делитесь рецептами и пробуйте новые 

### Сервис доступен по адресу:
```
([https://fooddotgram.ddns.net](https://fooddotgram.ddns.net/recipes))
```

### Возможности сервиса:
- делитесь своими рецептами
- смотрите рецепты других пользователей
- добавляйте рецепты в избранное
- быстро формируйте список покупок, добавляя рецепт в корзину
- следите за своими друзьями и коллегами

### Технологии:
- Django
- Python
- Docker

### Запуск проекта:
1. Клонируйте репозиторий:
```
git clone git@github.com:skillcrafter/foodgram-project-react.git
```
2. Подготовьте сервер:
```
scp docker-compose.yml <username>@<host>:/home/<username>/
scp nginx.conf <username>@<host>:/home/<username>/
scp .env <username>@<host>:/home/<username>/
```
3. Установите docker и docker-compose:
```
sudo apt install docker.io 
sudo apt install docker-compose
```
4. Соберите контейнер и выполните миграции:
```
sudo docker-compose up -d --build
sudo docker-compose exec backend python manage.py migrate
 sudo docker exec infra_backend_1 python manage.py makemigrations
 sudo docker exec infra_backend_1 python manage.py migrate

! sudo docker exec foodgram-backend-1 python manage.py makemigrations
! sudo docker exec foodgram-backend-1 python manage.py migrate
```
5. Создайте суперюзера и соберите статику:
```
sudo docker-compose exec backend python manage.py createsuperuser
sudo docker-compose exec backend python manage.py collectstatic --no-input
 sudo docker exec -it infra_backend_1 python manage.py createsuperuser
 sudo docker exec infra_backend_1 python manage.py collectstatic --no-input
! sudo docker exec foodgram-backend-1 python manage.py createsuperuser
! sudo docker exec foodgram-backend-1 python manage.py collectstatic --no-input
! sudo docker exec foodgram-backend-1 cp -r /app/collected_static/. /static/static/
```
6. - Наполнить базу данных тегами и ингредиентами:
```
sudo docker compose exec backend python manage.py load_data_tag
sudo docker compose exec backend python manage.py load_data_ingrediend
 sudo docker exec infra_backend_1 python manage.py load_data_tag
 sudo docker exec infra_backend_1 python manage.py load_data_ingrediend
! sudo docker exec foodgram-backend-1 python manage.py load_data_tag
! sudo docker exec foodgram-backend-1 python manage.py load_data_ingrediend
```
7. Данные для проверки работы приложения:
Суперпользователь:
```
- Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления
```

### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха

### Запуск проекта на локальной машине:

- Клонировать репозиторий:
```
git clone git@github.com:gratefultolord/foodgram-project-react.git
```

- В директории infra создать файл .env и заполнить своими данными по аналогии с example.env:
```
DB_ENGINE=django.db.postgresql
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=foodgram
DB_HOST=127.0.0.1
DB_PORT=5432
DEBUG=False
SECRET_KEY='секретный ключ Django'
```

- Создать и запустить контейнеры Docker, последовательно выполнить команды по созданию миграций, сбору статики, 
созданию суперпользователя, как указано выше.
```
docker-compose up -d
```
```
- После запуска проект будут доступен по адресу: [http://localhost/](http://localhost/)
```



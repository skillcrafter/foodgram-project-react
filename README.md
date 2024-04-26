# Продуктовый помощник. Включает в себя функции создания рецептов, сохранения 
# их в избранное, добавления в корзину покупок, которую можно скачать 
### в формате txt. Также есть возможность подписки на других авторов.
### Делитесь рецептами и пробуйте новые 

### Сервис доступен по адресу:
```
([https://foodgram-so.ddns.net/])
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
- Gunicorn
- Nginx

### Запуск проекта:
1. Клонируйте репозиторий:
```
git clone git@github.com:skillcrafter/foodgram-project-react.git
```
2. Установить на сервере Docker, Docker Compose:
```
sudo apt install curl                                   # установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      # скачать скрипт для установки
sh get-docker.sh                                        # запуск скрипта
sudo apt-get install docker-compose-plugin              # последняя версия docker compose
```
3. Соберите контейнер и выполните миграции:
```
sudo docker-compose up -d --build
sudo docker exec infra_backend_1 python manage.py makemigrations
sudo docker exec infra_backend_1 python manage.py migrate

```
4. Создайте суперюзера и соберите статику:
```
sudo docker exec infra-backend-1 python manage.py createsuperuser
sudo docker exec infra-backend-1 python manage.py collectstatic --no-input
sudo docker exec infra-nginx-1 cp -r /var/html/static/. /usr/share/nginx/html/static
```
5. - Наполнить базу данных тегами и ингредиентами:
```
sudo docker exec infra_backend_1 python manage.py load_data_tag
sudo docker exec infra_backend_1 python manage.py load_data_ingrediend
```
6. Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления
```

### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов nginx, frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха

### Запуск проекта на локальной машине:

- Клонировать репозиторий:
```
git clone git@github.com:skillcrafter/foodgram-project-react.git
```

- В директории infra создать файл .env и заполнить своими данными:
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
### Автор:

Ольга Степанова
YaMDb — это платформа для сбора отзывов пользователей на различные произведения (книги, фильмы, музыкальные альбомы). Сами произведения делятся на категории (например, «Книги» или «Фильмы») и жанры. Пользователи могут ставить произведениям оценки по десятибалльной шкале, писать развернутые отзывы, а также комментировать отзывы других пользователей. На основе оценок система автоматически рассчитывает усредненный рейтинг каждого произведения.

Установка и запуск проекта локально

    Клонируйте репозиторий на локальную машину:
    Bash

    git clone https://github.com/soroka-ilya/api_yamdb.git
    cd api_yamdb

    Cоздайте и активируйте виртуальное окружение:

        Для Windows:
        Bash

        python -m venv venv
        source venv/Scripts/activate

        Для Linux/macOS:
        Bash

        python3 -m venv venv
        source venv/bin/activate

    Установите зависимости из файла requirements.txt:
    Bash

    pip install --upgrade pip
    pip install -r requirements.txt

    Выполните миграции для создания структуры базы данных:
    Bash

    python manage.py makemigrations
    python manage.py migrate

    Запустите локальный сервер разработки:
    Bash

    python manage.py runserver

    Сервер будет доступен по адресу: http://127.0.0.1:8000/


Примеры запросов к API
1. Регистрация нового пользователя

    Запрос: POST /api/v1/auth/signup/

    Тело запроса (JSON):
    JSON

    {
      "username": "ivan_ivanov",
      "email": "ivanov@example.com"
    }

    Ответ (Status 200 OK):
    JSON

    {
      "username": "ivan_ivanov",
      "email": "ivanov@example.com"
    }

    (На указанный email будет отправлен секретный код подтверждения confirmation_code)

2. Получение JWT-токена

    Запрос: POST /api/v1/auth/token/

    Тело запроса (JSON):
    JSON

    {
      "username": "ivan_ivanov",
      "confirmation_code": "JWT-activation-code-from-email"
    }

    Ответ (Status 200 OK):
    JSON

    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

3. Получение списка произведений (Доступно без токена)

    Запрос: GET /api/v1/titles/

    Ответ (Status 200 OK):
    JSON

    [
      {
        "id": 1,
        "name": "Властелин Колец",
        "year": 1954,
        "rating": 10,
        "description": "Эпическое фэнтези",
        "genre": [
          {
            "name": "Фэнтези",
            "slug": "fantasy"
          }
        ],
        "category": {
          "name": "Книги",
          "slug": "books"
        }
      }
    ]
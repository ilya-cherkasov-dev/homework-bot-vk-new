# homework-bot-vk

VK-бот-ассистент, который следит за статусом проверки домашних работ в
Яндекс Практикуме и присылает уведомления в VK.

## Что умеет бот

- раз в 10 минут опрашивает API сервиса Практикум Домашка;
- при изменении статуса работы отправляет уведомление в VK;
- ведёт журнал событий (логирование) и сообщает о важных сбоях в VK.

## Технологии

- Python 3.14
- requests
- vk_api
- python-dotenv

## Как запустить

1. Клонировать репозиторий и перейти в его папку:

   ```bash
   git clone https://github.com/ilya-cherkasov-dev/homework-bot-vk-new.git
   cd homework-bot-vk-new
   ```

2. Создать и активировать виртуальное окружение:

   ```bash
   python -m venv venv
   # Windows
   . venv/Scripts/activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Установить зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создать файл `.env` в корне проекта (по образцу `.env.example`) и
   заполнить его своими значениями:

   ```env
   PRACTICUM_TOKEN=ваш_токен_практикума
   VK_TOKEN=токен_сообщества_vk
   VK_USER_ID=ваш_числовой_id_vk
   ```

5. Запустить бота:

   ```bash
   python homework.py
   ```

## Переменные окружения

| Переменная        | Назначение                                  |
|-------------------|---------------------------------------------|
| `PRACTICUM_TOKEN` | токен API Практикум Домашки                 |
| `VK_TOKEN`        | ключ доступа сообщества VK                  |
| `VK_USER_ID`      | числовой id пользователя, кому слать логи   |

## Автор

Ilya Cherkasov

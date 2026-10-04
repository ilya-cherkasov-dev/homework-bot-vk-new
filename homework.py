import logging
import os
import random
import sys
import time
from http import HTTPStatus

import requests
import vk_api
from dotenv import load_dotenv

from exceptions import ApiRequestError, WrongResponseCodeError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
VK_TOKEN = os.getenv('VK_TOKEN')
VK_USER_ID = os.getenv('VK_USER_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)


def check_tokens():
    """Проверить наличие всех обязательных переменных окружения."""
    return all((PRACTICUM_TOKEN, VK_TOKEN, VK_USER_ID))


def send_message(vk, message):
    """Отправить сообщение в VK-чат пользователю VK_USER_ID."""
    vk.messages.send(
        user_id=VK_USER_ID,
        message=message,
        random_id=random.randint(1, 2 ** 31),
    )
    logging.debug(f'Бот отправил сообщение: "{message}"')


def get_api_answer(timestamp):
    """Сделать запрос к API и вернуть ответ, приведённый к типам Python."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise ApiRequestError(
            f'Сбой при запросе к эндпоинту {ENDPOINT}: {error}'
        )
    if response.status_code != HTTPStatus.OK:
        raise WrongResponseCodeError(
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Проверить ответ API на соответствие ожидаемой структуре."""
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ API должен быть словарём, получен '
            f'{type(response).__name__}.'
        )
    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ "homeworks".')
    if 'current_date' not in response:
        raise KeyError('В ответе API отсутствует ключ "current_date".')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            'Данные под ключом "homeworks" должны быть списком, получен '
            f'{type(homeworks).__name__}.'
        )
    return homeworks


def parse_status(homework):
    """Извлечь статус домашней работы и подготовить сообщение для VK."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе API отсутствует ключ "homework_name".')
    homework_name = homework['homework_name']
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус домашней работы: "{status}".')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Отсутствует обязательная переменная окружения. '
            'Программа принудительно остановлена.'
        )
        sys.exit('Отсутствует обязательная переменная окружения.')

    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    timestamp = int(time.time())
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != last_message:
                    send_message(vk, message)
                    last_message = message
            else:
                logging.debug('В ответе нет новых статусов домашних работ.')
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != last_message:
                try:
                    send_message(vk, message)
                    last_message = message
                except Exception as send_error:
                    logging.error(
                        'Не удалось отправить сообщение об ошибке в VK: '
                        f'{send_error}'
                    )
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

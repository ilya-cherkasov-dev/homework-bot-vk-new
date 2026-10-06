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

TOKEN_NAMES = ('PRACTICUM_TOKEN', 'VK_TOKEN', 'VK_USER_ID')


def check_tokens():
    """Проверить наличие всех обязательных переменных окружения."""
    missing_tokens = [name for name in TOKEN_NAMES if not globals()[name]]
    if missing_tokens:
        logging.critical(
            'Отсутствуют обязательные переменные окружения: '
            f'{", ".join(missing_tokens)}.'
        )
    return not missing_tokens


def send_message(vk, message):
    """Отправить сообщение в VK и вернуть True при успешной отправке."""
    try:
        vk.messages.send(
            user_id=VK_USER_ID,
            message=message,
            random_id=random.randint(1, 2 ** 31),
        )
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в VK: {error}')
        return False
    logging.debug(f'Бот отправил сообщение: "{message}"')
    return True


def get_api_answer(timestamp):
    """Сделать запрос к API и вернуть ответ, приведённый к типам Python."""
    params = {'from_date': timestamp}
    logging.debug(f'Отправляем запрос к {ENDPOINT} с параметрами {params}.')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise ApiRequestError(
            f'Сбой при запросе к эндпоинту {ENDPOINT} '
            f'с параметрами {params}: {error}'
        )
    if response.status_code != HTTPStatus.OK:
        raise WrongResponseCodeError(
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}'
        )
    logging.debug('Ответ от API успешно получен.')
    return response.json()


def check_response(response):
    """Проверить ответ API на соответствие ожидаемой структуре."""
    logging.debug('Начинаем проверку ответа API.')
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ API должен быть словарём, получен '
            f'{type(response).__name__}.'
        )
    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ "homeworks".')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            'Данные под ключом "homeworks" должны быть списком, получен '
            f'{type(homeworks).__name__}.'
        )
    logging.debug('Ответ API прошёл проверку.')
    return homeworks


def parse_status(homework):
    """Извлечь статус домашней работы и подготовить сообщение для VK."""
    logging.debug('Начинаем проверку статуса домашней работы.')
    if 'homework_name' not in homework:
        raise KeyError('В ответе API отсутствует ключ "homework_name".')
    if 'status' not in homework:
        raise KeyError('В ответе API отсутствует ключ "status".')
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус домашней работы: "{status}".')
    logging.debug(f'Получен статус работы "{homework_name}": {status}.')
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{HOMEWORK_VERDICTS[status]}'
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Программа принудительно остановлена.')

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
                if message != last_message and send_message(vk, message):
                    last_message = message
            else:
                logging.debug('В ответе нет новых статусов домашних работ.')
            timestamp = response.get('current_date', int(time.time()))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            if message != last_message and send_message(vk, message):
                last_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s [%(levelname)s] '
            '%(funcName)s:%(lineno)d - %(message)s'
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    main()

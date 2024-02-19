import asyncio
import datetime

import gspread
import gspread_asyncio
from gspread.utils import rowcol_to_a1

from config_data.config import BASE_DIR, config
from database.db import User, History


from config_data.config import LOGGING_CONFIG
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


def read_user_from_table():
    json_file = BASE_DIR / 'credentials.json'
    gc = gspread.service_account(filename=json_file)
    url = config.tg_bot.USER_TABLE_URL
    sheet = gc.open_by_url(url)
    table = sheet.get_worksheet(0)
    values = table.get_values('A:BA')[2:]
    # logger.debug(f'values: {values}')
    users = {}

    for row in values:
        try:
            # logger.debug(f'row: {row}')
            rieltor_code = row[0]
            phone = row[1] or '-'
            fio = row[2] or '-'
            city = row[-1]
            is_delete = bool(row[-2])
            users[rieltor_code] = {
                'phone': phone,
                'fio': fio,
                'is_delete': is_delete,
                'city': city
            }
            # print(row)
            # print(len(row))
            # for num, val in enumerate(row):
            #     print(num, val)

            for num, i in enumerate(range(4, 32, 3), 1):
                value = row[i] or '1999-01-01'
                date = datetime.date.fromisoformat(value)
                users[rieltor_code][f'day{num}'] = date
            for num, i in enumerate(range(34, 50, 3), 1):
                value = row[i] or '1999-01-01'
                date = datetime.date.fromisoformat(value)
                users[rieltor_code][f'date{num}'] = date
        except Exception as err:
            err_log.error(f'Ошибка при чтении строки {row}')
    return users

from google.oauth2.service_account import Credentials


def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    json_file = BASE_DIR / 'credentials.json'
    creds = Credentials.from_service_account_file(json_file)
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


async def load_range_values(url=config.tg_bot.USER_TABLE_URL, sheets_num=0, diap='А:А'):
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    agc = await agcm.authorize()
    url = url
    sheet = await agc.open_by_url(url)
    table = await sheet.get_worksheet(sheets_num)
    values = await table.get_values(diap)
    return values


async def read_stats_from_table():
    """
    Читает таблицу статистики пользователей.
    :return: Словарь со статистикой с ключом rieltor_code
    {'date': '11.09.2023',
     '133845': {'ФИО сотрудника': 'Альмаганбетов Алибек Дюсенбаевич', 'Категория': '0-3', 'Рейтинг': '15', 'Интегральный показатель': '81%', 'Заявки на покупку, план': '15', 'Заявки на покупку, факт': '30', 'Объекты в базе (активные), план': '30', 'Объекты в базе (активные), факт': '23', 'Консультации по ипотеке, план': '5', 'Консультации по ипотеке, факт': '4', 'Заявки в банк по ипотеке, план': '3', 'Заявки в банк, факт': '3', 'Подборки, план': '14', 'Подборки, факт': '42', 'Показы (покупатель), план': '9', 'Показы (покупатель), факт': '0'}, '1245788276': {'ФИО сотрудника': 'Алмазова Анна Дмитриевна', 'Категория': '4+', 'Рейтинг': '', 'Интегральный показатель': '', 'Заявки на покупку, план': '', 'Заявки на покупку, факт': '', 'Объекты в базе (активные), план': '', 'Объекты в базе (активные), факт': '', 'Консультации по ипотеке, план': '', 'Консультации по ипотеке, факт': '', 'Заявки в банк по ипотеке, план': '', 'Заявки в банк, факт': '', 'Подборки, план': '', 'Подборки, факт': '', 'Показы (покупатель), план': '', 'Показы (покупатель), факт': ''},
     '1233': {'ФИО сотрудника': 'Москвитин Антон Валерьевич', 'Категория': 'Первая неделя', 'Рейтинг': '', 'Интегральный показатель': '', 'Заявки на покупку, план': '', 'Заявки на покупку, факт': '', 'Объекты в базе (активные), план': '', 'Объекты в базе (активные), факт': '', 'Консультации по ипотеке, план': '', 'Консультации по ипотеке, факт': '', 'Заявки в банк по ипотеке, план': '', 'Заявки в банк, факт': '', 'Подборки, план': '', 'Подборки, факт': '', 'Показы (покупатель), план': '', 'Показы (покупатель), факт': '', 'Затраты на рекламу, план': '', 'Затраты на рекламу, факт': '', 'Город': 'Тюмень'}
    """
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    agc = await agcm.authorize()
    url = config.tg_bot.USER_STAT_URL
    sheet = await agc.open_by_url(url)
    table = await sheet.get_worksheet(0)
    values = await table.get_values('A:U')
    columns_name = values[0]
    stat_dict = {}
    date = columns_name[0]
    stat_dict['date'] = date
    for row in values[1:]:
        user_dict = {}
        user_rieltor_code = row[1]
        for col_index, value in enumerate(row[2:], 2):
            key = columns_name[col_index]
            user_dict[key] = value
        stat_dict[user_rieltor_code] = user_dict
    return stat_dict


async def write_stats_from_table(rows):
    """
    Экспортирует данные пользователей User в таблицу сбор CSI
    :param rows:
    :return:
    """
    # logger.debug(f'Добавляем {rows}')
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    agc = await agcm.authorize()
    url = config.tg_bot.USER_TABLE_URL
    sheet = await agc.open_by_url(url)
    table = await sheet.get_worksheet(1)
    # await table.append_rows(rows)
    num_rows = len(rows)
    num_col = len(rows[0])
    logger.debug(f'{rowcol_to_a1(2 , 1)}:{rowcol_to_a1(1 + num_rows, num_col)}')
    await table.batch_update([{
        'range': f'{rowcol_to_a1(2 , 1)}:{rowcol_to_a1(1 + num_rows, num_col)}',
        'values': rows,
    }])


async def add_log_to_gtable(user: User, text: str):
    """
    Сохраняет движения пользователя в таблицу Логи
    :param user:
    :param text:
    :return:
    """
    try:
        logger.debug(f'Добавляем history в таблицу{text}')
        agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        agc = await agcm.authorize()
        url = config.tg_bot.USER_TABLE_URL
        sheet = await agc.open_by_url(url)
        table = await sheet.get_worksheet(2)
        await table.append_row([
            datetime.datetime.now().isoformat(sep=' ')[:-7],
            user.username,
            text])
    except Exception as err:
        logger.debug(err)



async def read_msg_from_table() -> dict:
    """
    Читает таблицу "Рассылка сообщений"
    :return: список для рассылки и текст сообщения
    {'senders': [],
     'text': 'Коллеги, пошаговая инструкция ',
     'city': 'Москва'
     }

    """
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    agc = await agcm.authorize()
    url = config.tg_bot.USER_TABLE_URL
    sheet = await agc.open_by_url(url)
    table = await sheet.get_worksheet(3)
    values = await load_range_values(sheets_num=3, diap='C2:D2')
    text = values[0][0]
    city = values[0][1]
    senders = await table.get_values('A:A')
    senders = [val[0] for val in senders]
    result = {
        'senders': senders,
        'text': text,
        'city': city
    }
    return result


async def get_user_code_from_city(city_to_send) -> set[str]:
    """
    Достает список кодов риэлторов с указанным городом
    :param city:
    :return:
    """
    users = await load_range_values(url=config.tg_bot.USER_STAT_URL, diap='A:U')
    users_rieltor_codes_to_send = set()
    for user in users:
        rieltor_code = user[1]
        user_city = user[-1]
        if user_city == city_to_send:
            users_rieltor_codes_to_send.add(rieltor_code)
    return users_rieltor_codes_to_send


async def get_codes_to_delete() -> set[str]:
    # Если в столбце AZ есть значение, считаем что удалять
    all_users = await load_range_values(diap='A:AZ')
    all_users = all_users[2:]
    codes_to_delete = set()
    for user in all_users:
        if user[-1]:
            codes_to_delete.add(user[0])
    return codes_to_delete


async def main():
    x = await read_stats_from_table()
    # print(x)
    for key, val in x.items():
        # print(key, type(key))
        if key == '1245785663':
            print(val)

if __name__ == '__main__':
    asyncio.run(main())


    # for u in y.items():
    #     print(u)
    #     break
    # print(y)
    # asyncio.run(write_stats_from_table())





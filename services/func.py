import asyncio
import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from database.db import Session, User, Menu, History
from config_data.config import LOGGING_CONFIG, config

import logging.config

from services.db_func import delete_user_from_tg_id
from services.google_func import read_stats_from_table, add_log_to_gtable

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


def check_user(id):
    """Возвращает найденных пользователей по tg_id"""
    logger.debug(f'Ищем юзера {id}')
    with Session() as session:
        user: User = session.query(User).filter(User.tg_id == str(id)).first()
        logger.debug(f'Результат: {user}')
        return user


def get_or_create_user(user) -> User:
    """Из юзера ТГ возвращает сущестующего User ли создает его"""
    try:
        tg_id = user.id
        username = user.username
        logger.debug(f'username {username}')
        old_user = check_user(tg_id)
        if old_user:
            logger.debug('Пользователь есть в базе')
            return old_user
        logger.debug('Добавляем пользователя')
        with Session() as session:
            new_user = User(tg_id=tg_id,
                            username=username,
                            register_date=datetime.datetime.now()
                            )
            session.add(new_user)
            session.commit()
            logger.debug(f'Пользователь создан: {new_user}')
        return new_user
    except Exception as err:
        err_log.error('Пользователь не создан', exc_info=True)


def update_user(tg_id, rieltor_code, g_user):
    logger.debug(f'Добавляем {(tg_id, rieltor_code, g_user)}')
    session = Session()
    with session:
        user: User = session.query(User).filter(User.tg_id == str(tg_id)).first()
        user.rieltor_code = rieltor_code
        for key, val in g_user.items():
            setattr(user, key, val)
        logger.debug(f'Юзер обновлен {user}')
        session.commit()


def get_menu_from_index(index) -> Menu:
    session = Session()
    with session:
        menu: Menu = session.query(Menu).filter(Menu.index == index).first()
        return menu


# def get_all_menu_items() -> Menu:
#     session = Session()
#     with session:
#         menu: Menu = session.query(Menu).filter().all()
#         return menu

def get_index_menu_from_text(text) -> str:
    """Достает индекс из меню по тексту"""
    if text == '⇤ Назад':
        return '0'
    session = Session()
    with session:
        menu: Menu = session.query(Menu).filter(Menu.text == text).first()
        return menu.index


def write_log(user_id, text):
    session = Session()
    try:
        with session:
            history: History = History(user_id=user_id, text=text, time=datetime.datetime.now())
            session.add(history)
            session.commit()
    except Exception as err:
        logger.error(err)
        err_log.error(err, exc_info=True)


def get_history(limit):
    session = Session()
    with session:
        historys = session.query(History).order_by(History.id.desc()).limit(limit).all()
        logger.debug(historys)
        return historys


def format_user_sats(user_dict, date: str):
    """{'ФИО сотрудника': 'Бабикова Анастасия Аркадьевна',
     'Категория': '0-3',
      'Рейтинг': '6',
       'Интегральный показатель': '78%',
        'Заявки на покупку, план': '15',
         'Заявки на покупку, факт': '11',
          'Объекты в базе (активные), план': '20',
           'Объекты в базе (активные), факт': '7',
            'Консультации по ипотеке, план': '3',
             'Консультации по ипотеке, факт': '3',
              'Заявки в банк по ипотеке, план': '1',
     'Заявки в банк, факт': '3',
      'Подборки, план': '11',
       'Подборки, факт': '10',
        'Показы (покупатель), план': '4',
         'Показы (покупатель), факт': '3',
          'Затраты на рекламу, план': '1100',
           'Затраты на рекламу, факт': '3',
            'Город': 'Омск'}"""
    """
        Ваши показатели на 29.08.2023*
        
        - Затраты на рекламу 1000 из 5000
        - Заявки на покупку с заполненной потребностью - 10 из 20
        - Объекты в базе (активные) - 30 из 40
        - Консультации по ипотеке - 10 из 15
        - Заявки в банк по ипотеке - 5 из 7
        - Подборки - 10 из 20
        - Показы (покупатель) - 10 из 20
        
        Интегральный показатель: 20%
        Вы занимаете 7 из 15 место в рейтинге города📈
        
        *показатели обновляются раз в неделю по понедельникам

    """
    print(user_dict)
    logger.debug(user_dict)
    logger.debug(f'Форматируем статистику: {user_dict}')
    msg = ''
    if user_dict['Категория'] == '0-3':
        msg = (f'Ваши показатели на {date}*\n\n'
               f"- Затраты на рекламу {user_dict['Затраты на рекламу, факт']} из {user_dict['Затраты на рекламу, план']}\n"
               f"- Заявки на покупку с заполненной потребностью - {user_dict['Заявки на покупку, факт']} из {user_dict['Заявки на покупку, план']}\n"
               f"- Объекты в базе (активные) - {user_dict['Объекты в базе (активные), факт']} из {user_dict['Объекты в базе (активные), план']}\n"
               f"- Консультации по ипотеке - {user_dict['Консультации по ипотеке, факт']} из {user_dict['Консультации по ипотеке, план']}\n"
               f"- Заявки в банк по ипотеке - {user_dict['Заявки в банк, факт']} из {user_dict['Заявки в банк по ипотеке, план']}\n"
               f"- Подборки - {user_dict['Подборки, факт']} из {user_dict['Подборки, план']}\n"
               f"- Показы (покупатель) - {user_dict['Показы (покупатель), факт']} из {user_dict['Показы (покупатель), план']}\n\n"
               f"<b>Интегральный показатель: {user_dict['Интегральный показатель']}</b>\n"
               f"Вы занимаете {user_dict['Рейтинг']} место в рейтинге города📈\n\n"
               )
    elif user_dict['Категория'] == 'Первая неделя':
        msg = (f'Ваши плановые показатели на {date}*\n\n'
               f"- Затраты на рекламу - {user_dict['Затраты на рекламу, план']}\n"
               f"- Заявки на покупку - {user_dict['Заявки на покупку, план']}\n"
               f"- Объекты в базе (активные) - {user_dict['Объекты в базе (активные), план']}\n"
               f"- Консультации по ипотеке - {user_dict['Консультации по ипотеке, план']}\n"
               f"- Заявки в банк по ипотеке - {user_dict['Заявки в банк по ипотеке, план']}\n"
               f"- Подборки - {user_dict['Подборки, план']}\n"
               f"- Показы (покупатель) - {user_dict['Показы (покупатель), план']}\n\n"
               )
    elif user_dict['Категория'] == '4+':
        msg = (f'Ваши показатели на {date}*\n\n'
               f"- Затраты на рекламу {user_dict['Затраты на рекламу, факт']}\n"
               f"- Заявки на покупку - {user_dict['Заявки на покупку, факт']}\n"
               f"- Объекты в базе (активные) - {user_dict['Объекты в базе (активные), факт']}\n"
               f"- Консультации по ипотеке - {user_dict['Консультации по ипотеке, факт']}\n"
               f"- Заявки в банк по ипотеке - {user_dict['Заявки в банк, факт']}\n"
               f"- Подборки - {user_dict['Подборки, факт']}\n"
               f"- Показы (покупатель) - {user_dict['Показы (покупатель), факт']}\n\n"
               )

    msg += '*показатели обновляются раз в неделю по понедельникам'
    return msg


async def send_message_to_manager(bot, user, text_msg):
    await bot.send_message(
        chat_id=config.tg_bot.GROUP_ID,
        # chat_id='EtagiManagers',
        text=(
            f'{text_msg}\n\n'
            f'#id{user.tg_id}\n'
            f'{user.fio}'
        ),
        parse_mode='HTML'
    )


async def send_report_to_users(users_to_send: list[User], bot: Bot):
    user_stats = await read_stats_from_table()
    for user in users_to_send:
        try:
            if user.rieltor_code in user_stats:
                logger.debug(f'Стата пользователя {user} найдена')
                text = format_user_sats(user_stats[user.rieltor_code],
                                        user_stats['date'])
                if text != '*показатели обновляются раз в неделю по понедельникам':
                    await bot.send_message(user.tg_id, text)
                    await asyncio.sleep(0.1)
                    logger.info(f'Сообщение пользователю {user.fio or user.tg_id} отправлено')
        except TelegramForbiddenError as err:
            logger.warning(f'Ошибка отправки сообщения для {user}: {err}')
            logger.info('Удаляем пользователя из базы')
            delete_user_from_tg_id(user.tg_id)
            log_text = f'Пользователь {user} удален из базы из-за {err}'
            logger.info(log_text)
            write_log(user.id, log_text)
            await add_log_to_gtable(user, log_text)
        except Exception as err:
            # await bot.send_message(config.tg_bot.admin_ids[0], 'Сообщение пользователю {user.fio or user.tg_id} НЕ отправлено')
            logger.error(f'ошибка отправки сообщения пользователю {user}: {err}', exc_info=False)
            err_log.error(f'ошибка отправки сообщения пользователю {user}: {err}', exc_info=True)

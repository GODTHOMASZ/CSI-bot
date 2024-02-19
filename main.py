import asyncio

import aioschedule
import schedule
from aiogram import Bot, Dispatcher

from config_data.config import LOGGING_CONFIG, config
from handlers import user_handlers, echo, csi_handlers, admin_handlers

import logging.config

from handlers.csi_handlers import send_csi_to_users
from lexicon.lexicon import LEXICON
from services.CSI import find_users_to_send, find_users_to_send_report
from services.db_func import clear_rieltor_code, get_user_from_rieltor_code, delete_user_from_codes
from services.func import send_report_to_users
from services.google_func import get_codes_to_delete, load_range_values

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


async def csi_week_job(bot):
    # Запрос анкетирования CSI
    tasks = find_users_to_send()
    logger.debug(f'Сегодня найдены пользовтаели для рассылки CSI date:\n{tasks}')
    await send_csi_to_users(bot, tasks, 'date')


async def csi_day_job(bot):
    # Запрос анкетирования CSI
    users_to_send = find_users_to_send()
    logger.debug(f'Сегодня найдены пользовтаели для рассылки CSI day:\n{users_to_send}')
    await send_csi_to_users(bot, users_to_send, 'day')


async def delete_user(bot):
    logger.info('Удаляем польззователей')
    codes_to_del = await get_codes_to_delete()
    logger.debug(f'Найдено пользователей: {codes_to_del}')
    del_count = delete_user_from_codes(codes_to_del)
    logger.info(f'Удалено: {del_count}')


async def send_report(bot):
    try:
        # Рассылка статистики по понедельникам
        logger.info('Рассылка статистики по понедельникам')
        users_to_send_report = find_users_to_send_report()
        logger.debug(f'Сегодня найдены пользовтаели для рассылки статистики:\n{users_to_send_report}')
        await send_report_to_users(users_to_send_report, bot)
        logger.debug('send_report выполнена')
    except Exception as err:
        logger.error(f'Рассылка статистики по понедельникам неудачна:', err)
        err_log.error(f'Рассылка статистики по понедельникам неудачна:', err, exc_info=True)


async def get_bad_values():
    bad_table = await load_range_values(url=config.tg_bot.USER_STAT_URL, sheets_num=8, diap='A:H')
    result = {}
    for row in bad_table[1:]:
        code = row[1]
        buy_bad = row[3]
        sell_bad = row[5]
        ipoteka_bad = row[7]
        result[code] = {'buy': buy_bad, 'sell': sell_bad, 'ipoteka': ipoteka_bad}
    return result


async def send_bad(bot, to_send, end_text):
    """
    Рассылка задач
    :param bot:
    :param to_send: [('1233', 'Отклонение по заявкам на покупку - 25%, Отклонение по заявкам в банк - 25%')]
    :param end_text:
    :return:
    """
    for task_to_send in to_send:
        # ('1233', 'Отклонение по заявкам на покупку - 25%, Отклонение по заявкам в банк - 25%')
        try:
            logger.debug(f'Отправка {task_to_send}')
            code, bad_text = task_to_send
            user = get_user_from_rieltor_code(code)
            text = f'“{user.fio.split()[1]}, добрый день! Обратите внимание, что у Вас отклонение по показателю:\n\n'
            text += bad_text + '\n'
            text += end_text
            await bot.send_message(chat_id=user.tg_id, text=text)
            logger.debug(f'Отправлено')
            await asyncio.sleep(0.2)
        except Exception as err:
            logger.error(f'Ошибка при отправке {task_to_send}: {err}')


async def buy(bot: Bot):
    """Начиная со 2-ой недели каждый вторник в 14:00 (мск) пользователю направляется сообщение с его отклонениями по покупке, также направляются рекомендации по исправлению показателей. Если отклонения отсутствуют, то они не направляются."""
    logger.debug('Отправка отклонений по продажам')
    bad_result = await get_bad_values()
    to_send = []
    # [('1233', 'Отклонение по заявкам на покупку - 25%, Отклонение по заявкам в банк - 25%')]
    for rieltor_code, bad_values in bad_result.items():
        bad_buy = bad_values.get('buy')
        if bad_buy:
            to_send.append((rieltor_code, bad_buy))
    logger.debug(f'Отклонения: {to_send}')
    end_text = LEXICON['buy_recomendation']
    await send_bad(bot, to_send, end_text)


async def sell(bot: Bot):
    """Начиная со 2-ой недели каждый вторник в 14:00 (мск) пользователю направляется сообщение с его отклонениями по покупке, также направляются рекомендации по исправлению показателей. Если отклонения отсутствуют, то они не направляются."""
    logger.debug('Отправка отклонений по продажам')
    bad_result = await get_bad_values()
    to_send = []
    # [('1233', 'Отклонение по заявкам на покупку - 25%, Отклонение по заявкам в банк - 25%')]
    for rieltor_code, bad_values in bad_result.items():
        bad_sell = bad_values.get('sell')
        if bad_sell:
            to_send.append((rieltor_code, bad_sell))
    logger.debug(f'Отклонения: {to_send}')
    end_text = LEXICON['sell_recomendation']
    await send_bad(bot, to_send, end_text)


async def ipoteka(bot: Bot):
    """Начиная со 2-ой недели каждую среду в 14:00 (мск) пользователю направляется сообщение с его отклонениями по ипотеке, также направляются рекомендации по исправлению показателей. Если отклонения отсутствуют, то они не направляются."""
    logger.debug('Отправка отклонений по продажам')
    bad_result = await get_bad_values()
    to_send = []
    # [('1233', 'Отклонение по заявкам на покупку - 25%, Отклонение по заявкам в банк - 25%')]
    for rieltor_code, bad_values in bad_result.items():
        bad_ipoteka = bad_values.get('ipoteka')
        if bad_ipoteka:
            to_send.append((rieltor_code, bad_ipoteka))
    logger.debug(f'Отклонения: {to_send}')
    end_text = LEXICON['ipoteka_recomendation']
    await send_bad(bot, to_send, end_text)


async def shedulers(bot):
    # aioschedule.every(5).minutes.do(job, bot)
    time_start1 = '9:00'
    aioschedule.every().day.at(time_start1).do(csi_week_job, bot)
    time_start2 = '15:00'
    aioschedule.every().day.at(time_start2).do(csi_day_job, bot)
    aioschedule.every().monday.at('11:00').do(send_report, bot)
    aioschedule.every().tuesday.at('11:00').do(buy, bot)
    aioschedule.every().wednesday.at('11:00').do(sell, bot)
    aioschedule.every().thursday.at('11:00').do(ipoteka, bot)
    aioschedule.every().day.at('5:00').do(delete_user, bot)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    logger.info('Starting bot Etagi')
    bot: Bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    # Регистриуем
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    dp.include_router(csi_handlers.router)
    dp.include_router(echo.router)
    asyncio.create_task(shedulers(bot))
    # await send_report(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await bot.send_message(
            config.tg_bot.admin_ids[0], f'Бот Этажи запущен.')
    except:
        err_log.critical(f'Не могу отравить сообщение {config.tg_bot.admin_ids[0]}')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
        # asyncio.run(buy(2))
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')
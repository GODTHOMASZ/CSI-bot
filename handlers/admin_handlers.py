import asyncio

from aiogram import Router, Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command, StateFilter, Text, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram.types import CallbackQuery, Message
from config_data.config import config
from database.db import History
from keyboards.keyboards import yes_no_kb
from services.db_func import get_users_to_send_message, get_user_from_rieltor_codes, \
    get_un_users, delete_user_from_tg_id
from services.func import get_history, check_user, write_log

from config_data.config import LOGGING_CONFIG
import logging.config

from services.google_func import read_msg_from_table, get_user_code_from_city, add_log_to_gtable

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        self.admins = config.tg_bot.admin_ids

    async def __call__(self, message: Message) -> bool:
        print(f'Проверка на админа\n'
              f'{message}\n'
              f'{message.from_user.id} in {self.admins}\n')
        return message.from_user.id in self.admins


router = Router()
router.message.filter(IsAdmin())


class FSMAdmin(StatesGroup):
    send_message = State()
    send_message_from_table = State()
    send_to_un_list = State()
    send_to_un_text = State()


@router.message(Command(commands=["history"]))
async def info(message: Message):
    history_list: list[History] = get_history(10)
    for hist in history_list:
        await message.answer(f'{hist.time}\n{hist.text}')


@router.message(Command(commands=["send_to_all"]))
async def command_send_to_all(message: Message,  state: FSMContext):
    logger.debug('/send_to_all')
    await message.answer(f'Найдено {len(get_users_to_send_message())} пользователей для рассылки\n\nВведите текст для рассылки всем пользователям:')
    await state.set_state(FSMAdmin.send_message)


# Обработка send_to_all
@router.message(StateFilter(FSMAdmin.send_message))
async def send_to_all(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    users = get_users_to_send_message()
    count = 0
    for user in users:
        try:
            await bot.send_message(user.tg_id, text)
            # await message.answer(F'Сообщение пользователю {user.fio or user.tg_id} отправлено')
            await asyncio.sleep(0.2)
            logger.info(f'Сообщение пользователю {user.fio or user.tg_id} отправлено')
            count += 1
        except TelegramForbiddenError as err:
            logger.warning(f'Ошибка отправки сообщения для {user}: {err}')
            logger.info(f'Удаляем пользователя {user} из базы')
            log_text = f'Пользователь {user} удален из базы из-за {err}'
            write_log(user, log_text)
            delete_user_from_tg_id(user.tg_id)
            await add_log_to_gtable(user, log_text)

        except Exception as err:
            # await message.answer(f'Сообщение пользователю {user.fio or user.tg_id} НЕ отправлено')
            err_log.error(f'ошибка отправки сообщения пользователю {user.tg_id}: {err}', exc_info=True)
    await message.answer(f'Сообщение отправлено {count} пользователям')
    await state.clear()


@router.message(Command(commands=["send"]))
async def command_send_to_all(message: Message,  state: FSMContext):
    logger.debug('/send')
    send_dict = await read_msg_from_table()
    senders = send_dict.get('senders')
    text = send_dict.get('text')
    logger.info(f'senders: {senders}')
    users = get_user_from_rieltor_codes(senders)
    if users:
        await message.answer(f'Найдено {len(users)} пользовтаелей')
        await message.answer(f'Сообщение для отправки:\n\n {text}')
        await message.answer('Отправить сообщение?', reply_markup=yes_no_kb(2))
        await state.set_state(FSMAdmin.send_message_from_table)
        await state.update_data(users=users, text=text)
    else:
        await message.answer(f'Не найдено пользователй для рассылки')


@router.message(Command(commands=["send_to_city"]))
async def command_send_to_all(message: Message,  state: FSMContext):
    logger.debug('/send_to_city')
    send_dict = await read_msg_from_table()
    city = send_dict.get('city')
    logger.debug(f'city: {city}')
    senders = await get_user_code_from_city(city)
    if senders:
        logger.debug(f'{len(senders)}')
    text = send_dict.get('text')
    logger.debug(f'{text}')
    users = get_user_from_rieltor_codes(senders)
    if users:
        await message.answer(f'Найдено пользователей из города {city}: {len(city)}')
        await message.answer(f'Сообщение для отправки:\n\n {text}')
        await message.answer('Отправить сообщение?', reply_markup=yes_no_kb(2))
        await state.set_state(FSMAdmin.send_message_from_table)
        await state.update_data(users=users, text=text)
    else:
        await message.answer(f'Не найдено пользователй из города {city}')


# Обработка send yes/no
@router.callback_query(StateFilter(FSMAdmin.send_message_from_table))
async def csi_answer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if callback.data == 'yes':
        data = await state.get_data()
        users = data['users']
        text = data['text']
        print(users)
        for user in users:
            try:
                if user and user.tg_id:
                    await bot.send_message(user.tg_id, text=text)
                    logger.info(f'Сообщение для {user} отправлено')
                    await asyncio.sleep(0.2)
                else:
                    logger.warning(f'Не могу отправить сообщения для {user} - id не найден')
            except TelegramForbiddenError as err:
                logger.warning(f'Ошибка отправки сообщения для {user}: {err}')
                logger.info('Удаляем пользователя из базы')
                log_text = f'Пользователь {user} удален из базы из-за {err}'
                logger.info(log_text)
                write_log(user.id, log_text)
                delete_user_from_tg_id(user.tg_id)
                await add_log_to_gtable(user, log_text)
            except Exception:
                err_log.error(f'Сообщение для {user} НЕ отправлено', exc_info=False)
    await callback.message.delete()
    await state.clear()


# Отправка по списку
@router.message(Command(commands=["send_to_un"]))
async def send_to_worker(message: Message, state: FSMContext, bot: Bot):
    logger.debug('/send_to_un')
    users_to_send = get_un_users()
    if users_to_send:
        await state.update_data(users_to_send=users_to_send)
        await message.answer(f'В базе найдено {len(users_to_send)} неавторизованных пользователей')
        await message.answer(f'Введите текст сообщения')
        await state.set_state(FSMAdmin.send_to_un_text)
    else:
        await state.clear()
        await message.answer('Не найдено пользователей в базе')


@router.message(StateFilter(FSMAdmin.send_to_un_text))
async def send_to_un_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    await state.update_data(text=message.text)
    await message.answer(f'Отправить сообщение?:\n<b>{text}</b>\n', reply_markup=yes_no_kb(2))


@router.callback_query(StateFilter(FSMAdmin.send_to_un_text))
async def send_to_worker_confirm(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await callback.message.delete()
    if callback.data == 'yes':
        data = await state.get_data()
        text = data['text']
        users = data['users_to_send']
        count = 0
        for user in users:
            try:
                await bot.send_message(user.tg_id, text)
                count += 1
                logger.info(f'Сообщение пользователю {user.fio or user.tg_id} отправлено')
                await asyncio.sleep(0.1)
            except TelegramForbiddenError as err:
                logger.warning(f'Ошибка отправки сообщения для {user}: {err}')
                logger.info('Удаляем пользователя из базы')
                log_text = f'Пользователь {user} удален из базы из-за {err}'
                logger.info(log_text)
                write_log(user.id, log_text)
                delete_user_from_tg_id(user.tg_id)
                await add_log_to_gtable(user, log_text)
            except Exception as err:
                err_log.error(f'ошибка отправки сообщения пользователю {user.tg_id} {err}', exc_info=False)
        await callback.message.answer(f'Сообщение разослано {count} пользователям')
    await state.clear()


@router.message(Command(commands=["ban"]))
async def command_send_to_all(message: Message,  state: FSMContext, bot: Bot):
    logger.debug('ban')
    try:
        chat_id = 395044844
        await bot.send_message(chat_id=chat_id, text='test ban')
    except TelegramForbiddenError as err:
        logger.warning(err)
        user = check_user(chat_id)
        logger.info(f'Удаляем пользователя {user} из базы')
        result = delete_user_from_tg_id(395044844)
        if result:
            logger.info(f'{user} удален')
        else:
            logger.warning(f'{user} не удален')
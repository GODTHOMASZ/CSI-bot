import aioschedule
from aiogram import Dispatcher, types, Router, Bot, F
from aiogram.filters import Command, CommandStart, Text, StateFilter, \
    BaseFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, URLInputFile

from aiogram.fsm.context import FSMContext

from database.db import History, Menu, User, Lexicon
from keyboards.keyboards import start_menu_kb, start_kb, contact_kb, \
    start_menu_kb2

from services.func import get_or_create_user, update_user, get_menu_from_index, \
    write_log, get_history, format_user_sats, send_message_to_manager, \
    get_index_menu_from_text, send_report_to_users, check_user
from services.google_func import read_user_from_table, read_stats_from_table, \
    add_log_to_gtable



from config_data.config import LOGGING_CONFIG, config
import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

router: Router = Router()


class FSMCheckUser(StatesGroup):
    send_phone = State()
    check_phone = State()
    input_rieltor_code = State()


class IsAuthorized(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, event_from_user, bot: Bot, *args, **kwargs) -> bool:
        if isinstance(message, CallbackQuery):
            message = message.message
        user = check_user(event_from_user.id)
        print(f'Авторизован: {user and user.rieltor_code}')
        if user and user.rieltor_code:
            return True
        return False


@router.message(Command(commands=["start"]))
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    user: User = get_or_create_user(tg_user)
    if not user.rieltor_code:
        # await message.answer('Нажмите "Поделиться телефоном" для авторизации',
        #                      reply_markup=contact_kb)
        await message.answer('Введите код риэлтора для авторизации')
        await state.set_state(FSMCheckUser.input_rieltor_code)
        await state.update_data(user=user)
    else:
        text = Lexicon.get('/start').format(user.fio.split()[1] or user.username)
        await message.answer(text, reply_markup=start_kb)
        await message.answer(Lexicon.get('menu_text'),
                             reply_markup=start_menu_kb2(1, '0'))
    log_text = f'{user.username or user.tg_id} {user.rieltor_code} нажал /start'
    await add_log_to_gtable(user, log_text)
    write_log(user.id, log_text)


# # Прием телефона
# @router.message(StateFilter(FSMCheckUser.send_phone))
# async def receive_phone(message: Message, state: FSMContext, bot: Bot):
#     print('Прием и проверка телефона')
#     if message.contact:
#         input_phone = message.contact.phone_number
#         await state.update_data(input_phone=input_phone)
#         await message.answer(f'Ваш телефон {input_phone}')
#         # Проверка телефона
#         users_from_table = read_user_from_table()
#         for rieltor_code, user_dict in users_from_table.items():
#             phone = user_dict['phone']
#             if phone != '-' and input_phone.strip()[-10:] in phone and not user_dict.get('is_delete'):
#                 print('eeeeee', rieltor_code, user_dict)
#                 update_user(message.from_user.id, rieltor_code, user_dict)
#                 log_text = f'{message.from_user.username or message.from_user.id} авторизовался по телефону {input_phone} как {rieltor_code}: {user_dict["fio"]}'
#                 data = await state.get_data()
#                 user = data['user']
#                 await add_log_to_gtable(user, log_text)
#                 write_log(user.id, log_text)
#                 await message.answer('Вы авторизовались!', reply_markup=start_kb)
#                 name = user_dict['fio'].split()
#                 if name and len(name) == 3:
#                     name = name[1]
#                 else:
#                     name = user_dict['fio']
#                 text = Lexicon.get('/start').format(name)
#                 await message.answer(text, reply_markup=start_kb)
#
#                 # Отправка показателей
#                 user_to_send = get_or_create_user(message.from_user)
#                 await send_report_to_users([user_to_send], bot)
#
#                 await state.clear()
#                 return
#         await message.answer('Ваш телефон не найден в базе, введите код риэлтора')
#         await state.set_state(FSMCheckUser.input_rieltor_code)
#     else:
#         await message.answer('Нажмите "Поделиться телефоном" для авторизации')


# Проверка rieltor_code, заполнение User
@router.message(StateFilter(FSMCheckUser.input_rieltor_code))
async def check_rieltor_code(message: Message, state: FSMContext, bot: Bot):
    try:
        input_rieltor_code = message.text.strip()
        users_from_table = read_user_from_table()
        if input_rieltor_code in users_from_table:
            if not users_from_table[input_rieltor_code].get('is_delete'):
                g_user: dict = users_from_table[input_rieltor_code]
                fio = g_user.get("fio")
                logger.debug(f'fio: {fio}')
                name = fio.split()
                logger.debug(f'name: {name}')
                if name and len(name) == 3:
                    name = name[1]
                else:
                    name = fio

                text = Lexicon.get('/start').format(name)
                await message.answer(text, reply_markup=start_kb)
                await state.clear()
                update_user(message.from_user.id, input_rieltor_code, g_user)
                log_text = f'{message.from_user.username or message.from_user.id} подтвердил rieltor_code {input_rieltor_code}'
                # data = await state.get_data()
                # user = data['user']
                user: User = get_or_create_user(message.from_user)
                await add_log_to_gtable(user, log_text)
                write_log(user.id, log_text)

                # ОТправка статистики
                user_to_send = get_or_create_user(message.from_user)
                await send_report_to_users([user_to_send], bot)
            else:
                await message.answer('Вы удалены из базы')
                await state.clear()
        else:
            await message.answer('Мы не нашли ваш код 😔 Обратитесь к администратору https://t.me/lilia_dddd  и мы вам поможем🤝')
            await state.clear()
    except Exception as err:
        logger.error(err, exc_info=True)
        await message.answer('При поиске кода произошла ошибка. Попробуйте снова написать /start или обратиться к администратору https://t.me/lilia_dddd')
        await state.clear()


@router.message(Text(text=["Меню"]))
async def process_menu(message: Message, state: FSMContext):
    await message.answer(Lexicon.get('menu_text'),
                         reply_markup=start_menu_kb2(1, '0'))


# Меню статистика
@router.callback_query(Text(text='startmenu:4'))
# @router.message(Command(commands=["info"]))
async def info(callback: CallbackQuery, state: FSMContext):
    message = callback.message
    user = get_or_create_user(callback.from_user)
    logger.debug(f'Пользователь: {user}, code: {user.rieltor_code}')
    user_stats = await read_stats_from_table()
    if user.rieltor_code in user_stats:
        logger.debug(f'Стата пользователя {user} найдена')
        text = format_user_sats(user_stats[user.rieltor_code], user_stats['date'])
        await message.answer(text)
    else:
        await message.answer('Вы не найдены в базе. Обратитесь к администратору')
    await message.delete()
    await add_log_to_gtable(user, f'{user.fio} запросил статистику')


class IsMenu(BaseFilter):
    def __init__(self) -> None:
        menu_items = []
        for menu_item in Menu.get_items('all'):
            menu_items.append(menu_item.text)
        self.menu_items = menu_items + ['⇤ Назад', 'Меню']
        print('Всем меню:', menu_items)

    async def __call__(self, message: Message) -> bool:
        print('Проверка на меню:')
        print(message.text in self.menu_items)
        return message.text in self.menu_items


# Обработка нажатий меню пользователя
@router.message(IsMenu())
async def send_menu(message: Message, bot: Bot):
    logger.debug('send_menu')
    if message.text == 'Мои показатели':
        user = get_or_create_user(message.from_user)
        logger.debug(f'Пользователь: {user}, emai: {user.rieltor_code}')
        user_stats = await read_stats_from_table()
        if user.rieltor_code in user_stats:
            logger.debug(f'Стата пользователя {user} найдена')
            text = format_user_sats(user_stats[user.rieltor_code],
                                    user_stats['date'])
            await message.answer(text, reply_markup=start_kb)
        else:
            await message.answer(
                'Вы не найдены в базе. Обратитесь к администратору',
                reply_markup=start_kb)
        await add_log_to_gtable(user, f'{user.fio} запросил статистику')
    else:
        index = get_index_menu_from_text(message.text)
        if index == '0':
            menu = Menu(index=None, text='Главное меню', is_with_children=1)
        else:
            menu: Menu = get_menu_from_index(index)
        user = get_or_create_user(message.from_user)
        log_text = f'{user.fio or user.username} {user.rieltor_code}: {menu.index}. {menu.text}'
        if menu.is_with_children:
            await message.answer(menu.text, reply_markup=start_menu_kb2(1, index))
        else:
            await message.answer(text=menu.navigation())
            await message.answer(Lexicon.get('menu_select'), reply_markup=start_kb)
            await send_message_to_manager(bot, user, menu.navigation())
        write_log(user.id, log_text)
        await add_log_to_gtable(user, log_text)

import asyncio
import datetime
import sys

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils.functions import database_exists, create_database


from config_data.config import config

# engine = create_engine(f"postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/{config.db.database}", echo=False)
# engine = create_engine(f"postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@localhost:{config.db.db_port}/{config.db.database}", echo=False)
# print(f"postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/{config.db.database}")
# Session = sessionmaker(bind=engine)
# db_url = f"postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@localhost:{config.db.db_port}/{config.db.database}"
db_url = f"postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/{config.db.database}"
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    tg_id: Mapped[str] = mapped_column(String(30))

    username: Mapped[str] = mapped_column(String(50), nullable=True)
    rieltor_code: Mapped[str] = mapped_column(String(50), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    fio: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=True)
    date1: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    date2: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    date3: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    date4: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    date5: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    date6: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    date1_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    date2_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    date3_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    date4_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    date5_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    date6_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    date1_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    date2_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    date3_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    date4_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    date5_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    date6_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day1: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day2: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day3: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day4: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day5: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day6: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day7: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day8: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day9: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day10: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    day1_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day2_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day3_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day4_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day5_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day6_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day7_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day8_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day9_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day10_csi: Mapped[int] = mapped_column(Integer(), nullable=True)
    day1_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day2_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day3_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day4_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day5_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day6_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day7_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day8_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day9_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    day10_comment: Mapped[str] = mapped_column(String(2000), nullable=True)
    history = relationship(
        "History",
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __repr__(self):
        return f'{self.id}. {self.tg_id} {self.username or "-"}. code: {self.rieltor_code or "-"}'


class Menu(Base):
    __tablename__ = 'menu_items'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    text: Mapped[str] = mapped_column(String(100), default='-')
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete='CASCADE'), default=None, nullable=True)
    is_with_children: Mapped[int] = mapped_column(
        Integer(), server_default='0', nullable=False)
    index: Mapped[str] = mapped_column(String(20))

    def __repr__(self):
        return f'{self.index}: {self.text} parent_id: {self.parent_id} is_with_children: {self.is_with_children}'

    def navigation(self):
        print(self.parent_id)
        session = Session()
        with session:
            parent_menu: Menu = session.query(Menu).filter(Menu.id == self.parent_id).one_or_none()
            print('parent_menu:', parent_menu)
        if parent_menu:
            return f'| {parent_menu.text} > {self.text}'
        else:
            return f'| {self.text}'

    @staticmethod
    def get_items(parent=None):
        _session = Session()
        with _session:
            if parent == 'all':
                _menu_items = session.query(Menu).filter().all()
            else:
                _menu_items = session.query(Menu).filter(Menu.parent_id == parent).all()
            return _menu_items


class History(Base):
    __tablename__ = 'history'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete='CASCADE'))
    user = relationship("User", back_populates="history")
    time: Mapped[datetime.datetime] = mapped_column(DateTime())
    text: Mapped[str] = mapped_column(String(250), nullable=True)

    def __repr__(self):
        return f'{str(self.time)[:-7]}: {self.text}'


class BotSettings(Base):
    __tablename__ = 'bot_settings'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    name: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(50), nullable=True, default='')
    description: Mapped[str] = mapped_column(String(255),
                                             nullable=True,
                                             default='')


class Lexicon(Base):
    __tablename__ = 'lexicon'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    name: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(String(1000))

    @staticmethod
    def get(key_name):
        _session = Session()
        try:
            with _session:
                lexicon = _session.query(Lexicon).filter(Lexicon.name == key_name).one_or_none()
                value = lexicon.text
                return value
        except Exception as err:
            raise err


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)


# Заполнение пустой базы
# index, text, parent_id, is_with_children
start_menu_list = [
    ['1', 'У меня есть сложности в обучении', None, 1],
    ['2', 'У меня есть сложности на практике', None, 1],
    ['3', 'Хочу узнать как поменять менеджера', None, 0],
    ['4', 'Мои показатели', None, 0],
    ['5', 'Другое', None, 0],

        ['1_1', 'Не хватает обучающих материалов', 1, None],
        ['1_2', 'Нужно больше практических примеров', 1, None],
        ['1_3', 'Не понимаю тему', 1, None],
        ['1_4', 'Другое', 1, None],

        ['2_1', 'Медленно набираю базу, хочу научиться делать это быстрее', 2, None],
        ['2_2', 'Сложно даются холодные звонки/ выгораю', 2, None],
        ['2_3', 'Выполняю активности, но нет желаемого результата', 2, None],
        ['2_4', 'Другое', 2, None],
]

session = Session()
with session:
    menu_items = session.query(Menu).all()
    print(menu_items)
    if not menu_items:
        for item_menu in start_menu_list:
            menu = Menu(
                index=item_menu[0],
                text=item_menu[1],
                parent_id=item_menu[2],
                is_with_children=item_menu[3]
                        )
            session.add(menu)
            session.commit()

    lexicon_items = session.query(Lexicon).all()
    print(lexicon_items)
    if not lexicon_items:
        for key in ['/start', 'csi_text', 'date1_text', 'date2_text', 'date3_text', 'date4_text', 'date5_text', 'date6_text', 'csi_5_text', 'csi_4_text', 'csi_1-3_text', 'menu_text', 'menu_select']:
            print(key)
            menu = Lexicon(name=key,
                           text=key)
            session.add(menu)
        session.commit()


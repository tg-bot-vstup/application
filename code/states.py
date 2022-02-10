from aiogram.dispatcher.filters.state import State, StatesGroup


class States(StatesGroup):
    """States of bot"""

    grade = State()
    choose_area = State()
    choose_spec = State()
    choose_region = State()
    choose_uni = State()
    search = State()
    choice_adding = State()
    add_from = State()

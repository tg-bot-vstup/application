from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)
from bot_controller import Controller


class Keyboard():
    ''' Keyboard for reply markups '''

    button_add = KeyboardButton('Додати оцiнки ЗНО')
    button_my = KeyboardButton('Мої бали')
    button_where = KeyboardButton('Куди я можу вступити?')

    home = ReplyKeyboardMarkup(resize_keyboard=True)
    home.add(button_add, button_my)
    home.add(button_where)

    choice = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True)
    yes = KeyboardButton('Так')
    no = KeyboardButton('Нi')
    back = KeyboardButton('Назад')
    choice.add(yes,no)
    choice.add('Назад')


class Buttons():
    '''Inline buttons'''

    regions = Controller.get_regions()
    select_region = InlineKeyboardMarkup(row_width=2)

    for region in regions:
        select_region.insert(InlineKeyboardButton(
            text=region.name, callback_data=region.id))

    def universities(region):
        # Getting list of universities by region
        universities = Controller.get_universities(region)
        select_uni = InlineKeyboardMarkup(row_width=2)

        for uni in universities:
            # Generation of buttons with universities

            select_uni.insert(InlineKeyboardButton(
                text=uni.name, callback_data=uni.id))

        return select_uni

    def areas(page):

        select_area = InlineKeyboardMarkup(row_width=2)
        areas = Controller.get_areas()
        areas = [area for area in areas if area.get('specs')]
        if len(areas) <= page*8+8:
            for area in areas[page*8:]:
                select_area.insert(InlineKeyboardButton(
                    text=area['name'], callback_data=area['name'][:15]))
        else:
            for area in areas[page*8:page*8+8]:
                select_area.insert(InlineKeyboardButton(
                    text=area['name'], callback_data=area['name'][:15]))
            select_area.insert(InlineKeyboardButton(
            text='Далi',callback_data=f'page_{page+1}'))
        if page != 0:
            select_area.add(InlineKeyboardButton(
            text='Назад',callback_data=f'page_{page-1}'))
        
        return select_area

    def get_specs(area):

        select_spec = InlineKeyboardMarkup(row_width=1)
        specialities = Controller.get_specs(area)

        for spec in specialities:
            select_spec.insert(InlineKeyboardButton(
                text=spec[0].name, callback_data=spec[0].name[:15]))

        return select_spec

    def configure_grades(user,grades):

        #grades = Controller.ma_balls(user)
        edit_grades_buttons = InlineKeyboardMarkup(row_width=2)
        for grade in grades:
            edit_grades_buttons.insert(
                InlineKeyboardButton(text=grade.zno.name,callback_data=f'set_{grade.zno.id}'))
        return edit_grades_buttons

    all_zno = Controller.get_znos()
    set_grade = InlineKeyboardMarkup(row_width=2)
    #Getting only zno subjects and attestat
    for zno in all_zno:
        set_grade.insert(InlineKeyboardButton(
            text=zno[1], callback_data=f'set_{zno[0]}'))

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from bot_controller import Controller


class Keyboard():
    ''' Keyboard for reply markups '''

    button_add = KeyboardButton('Додати оцiнки ЗНО')
    button_my = KeyboardButton('Мої бали')
    button_where = KeyboardButton('Куди я можу вступити?')

    home = ReplyKeyboardMarkup(resize_keyboard=True)
    home.add(button_add, button_my)
    home.add(button_where)


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

    def areas():

        select_area = InlineKeyboardMarkup(row_width=2)
        areas = Controller.get_areas()
        print(areas)

        for area in areas:
            if area.specialities:
                select_area.insert(InlineKeyboardButton(
                    text=area.name,callback_data=area.name[:15]))

        return select_area

    def get_specs(area):

        select_spec = InlineKeyboardMarkup(row_width=2)
        specialities = Controller.get_specs(area)

        for spec in specialities:
            print(spec[0])
            select_spec.insert(InlineKeyboardButton(    
                text=spec[0].name,callback_data=spec[0].name[:15]))

        return select_spec

    znos = Controller.get_znos()
    set_grade = InlineKeyboardMarkup(row_width=2)

    for zno in znos:
        if zno.id <= 9 or zno.id == 14:
            set_grade.insert(InlineKeyboardButton(
                text=zno.name,callback_data=zno.id))
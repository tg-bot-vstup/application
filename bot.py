from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from bot_controller import Controller
from keyboards import Keyboard, Buttons
from states import States
from dotenv import load_dotenv
from utils import get_zno
import os

load_dotenv()
bot = Bot(token=os.environ.get('TOKEN'))
db_cont = Controller()
dp = Dispatcher(bot, storage=MemoryStorage())

''' Message Handlers '''


@dp.message_handler(commands=['help', 'start'], state='*')
async def hello(message: types.Message):
    await message.answer(
        'Привiт! Цей бот допоможе вам дiзнатись куди ви можете поступити!',
        reply_markup=Keyboard.home)
    db_cont.create_user(message.from_user.id)


@dp.message_handler(Text(equals='Назад'), state='*')
async def hello(message: types.Message):
    await message.answer('Повертаємось до головного меню',
                         reply_markup=Keyboard.home)
    db_cont.create_user(message.from_user.id)


@dp.message_handler(Text(equals='Куди я можу вступити?', ignore_case=True), state='*')
async def get_regions(message: types.Message):

    await message.answer("Оберiть ваш регiон:",
                         reply_markup=Buttons.select_region)
    await States.choose_region.set()


@dp.message_handler(Text(equals='Мої бали', ignore_case=True), state='*')
async def get_grades(message: types.Message):

    grades = Controller.ma_balls(message.from_user.id)
    await message.answer('\n'.join(grades))


@dp.message_handler(state=States.grade)
async def get_grades(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        zno_id = data['zno_id']

        try:
            data['grade'] = float(message.text)

            if (data['grade'] >= 100 and data['grade'] <= 200) or data['grade'] == 0:
                print(data['grade'])
                await message.answer(Controller.set_grade(
                        message.from_user.id, zno_id, data['grade']),
                    reply_markup=Keyboard.home)
                await state.finish()

            else:
                raise ValueError

        except ValueError:
            await message.answer('Невiрне значення. Спробуйте ще раз.')


@dp.message_handler(Text(equals='Додати оцiнки ЗНО', ignore_case=True), state='*')
async def set_grades(message: types.Message, state: FSMContext):
    # checking current state and finish it
    if await state.get_state() is not None:
        await state.finish()
    await message.answer("Оберiть предмет",
                         reply_markup=Buttons.set_grade)

''' Callback Handlers part '''

'''
@dp.callback_query_handler(Text(equals('back')), state='*')
async def go_back(callback_query: types.CallbackQuery, state: FSMContext):
    if await state.get_state() is not None:
        state.finish()
    await callback_query.message.answer(
        'Повертаємось в головне меню...',
        reply_markup=Keyboard.home)
    await callback_query.answer()
'''


@dp.callback_query_handler(state=States.choose_region)
async def choose_area(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['region'] = callback_query.data
    await callback_query.message.edit_text('Зачекайте...')
    areas = Buttons.areas()  # Var for faster edit after
    await callback_query.message.edit_text('Оберiть галузь знань')
    await callback_query.message.edit_reply_markup(areas)
    await States.choose_spec.set()
    await callback_query.answer()


@dp.callback_query_handler(state=States.choose_spec)
async def choose_area(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Оберiть Спеціальність')
    await callback_query.message.edit_reply_markup(
        Buttons.get_specs(callback_query.data))
    await States.search.set()
    await callback_query.answer()

@dp.callback_query_handler(state=States.search)
async def choose_area(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['spec'] = callback_query.data
    await callback_query.message.edit_text('Рахуемо...')
    Controller.get_chances(
        callback_query.from_user.id,
        data['region'],
        data['spec'])
    await callback_query.answer()

@dp.callback_query_handler(Text(startswith='set'), state='*')
async def set_zno_grade(callback_query: types.CallbackQuery, state: FSMContext):
    newdata = dict(callback_query.message.reply_markup).get('inline_keyboard')
    # Getting zno name from data instead of search in database
    zno_name = get_zno(newdata, callback_query.data)

    '''Add zno subject to local data'''
    async with state.proxy() as data:
        data['zno_id'] = callback_query.data.split('_')[1]

    await callback_query.message.answer(
        f'Введiть балл з: {zno_name}\nДля видалення введiть 0',
        reply_markup=types.ReplyKeyboardMarkup(
            resize_keyboard=True).add(types.KeyboardButton('Назад')))
    await callback_query.answer()
    await States.grade.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

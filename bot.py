from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from bot_controller import Controller
from keyboards import Keyboard, Buttons
from states import States
from dotenv import load_dotenv
import os

load_dotenv()
bot = Bot(token=os.environ.get('TOKEN'))
db_cont = Controller()
dp = Dispatcher(bot, storage=MemoryStorage())

''' Message Handlers '''


@dp.message_handler(commands=['help', 'start'], state='*')
async def hello(message: types.Message):
    await message.answer('''
        Привiт! Цей бот допоможе вам дiзнатись куди ви можете поступити!''',
                         reply_markup=Keyboard.home)
    db_cont.create_user(message.from_user.id)


@dp.message_handler(Text(equals='Куди я можу вступити?', ignore_case=True), state='*')
async def get_grades(message: types.Message):

    await message.answer("Оберiть ваш регiон:",
                         reply_markup=Buttons.select_region)
    await States.choose_region.set()


@dp.message_handler(Text(equals='Мої бали', ignore_case=True), state='*')
async def get_grades(message: types.Message):

    print(Controller.ma_balls(message.from_user.id))


@dp.message_handler(Text(equals='Додати оцiнки ЗНО', ignore_case=True), state='*')
async def set_grades(message: types.Message):
    await States.grade.set()
    await message.answer("Оберiть предмет",
                         reply_markup=Buttons.set_grade)

''' Callback Handlers part '''


@dp.callback_query_handler(state=States.choose_region)
async def choose_area(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['region'] = callback_query.data
    await callback_query.message.edit_text('Оберiть галузь знань')
    await callback_query.message.edit_reply_markup(Buttons.areas())
    await States.choose_spec.set()
    await callback_query.answer()


@dp.callback_query_handler(state=States.choose_spec)
async def choose_area(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['k_area'] = callback_query.data
    await callback_query.message.edit_text('Оберiть Спеціальність')
    await callback_query.message.edit_reply_markup(
        Buttons.get_specs(callback_query.data))
    await state.finish()
    await callback_query.answer()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

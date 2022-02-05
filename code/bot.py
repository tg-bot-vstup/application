from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from bot_controller import Controller
from keyboards import Keyboard, Buttons
from states import States
from dotenv import load_dotenv
from utils import get_zno, result_generation,validate_grade
import os
from time import sleep
import asyncio

load_dotenv()
bot = Bot(token=os.environ.get('TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

''' Message Handlers '''


@dp.message_handler(commands=['help', 'start'], state='*')
async def hello(message: types.Message):
    await message.answer(
        'Привiт! Цей бот допоможе вам дiзнатись куди ви можете поступити!',
        reply_markup=Keyboard.home)
    Controller.create_user(message.from_user.id)


@dp.message_handler(Text(equals='Назад'), state='*')
async def hello(message: types.Message,state: FSMContext):
    if state.get_state():
        state.finish()
    await message.answer('Повертаємось до головного меню',
                         reply_markup=Keyboard.home)


@dp.message_handler(Text(equals='Куди я можу вступити?', ignore_case=True), state='*')
async def get_regions(message: types.Message):

    await message.answer("Оберiть ваш регiон:",
                         reply_markup=Buttons.select_region)
    await States.choose_region.set()


@dp.message_handler(Text(equals='Мої бали', ignore_case=True), state='*')
async def get_grades(message: types.Message, state=FSMContext):
    if await state.get_state():
        await state.finish()
    grades = Controller.ma_balls(message.from_user.id)
    n = '\n'  # variable bcs f-string can't handle backslash
    if grades:
        gradez = [str(grade) for grade in grades]
       
        await message.answer(f'''{n.join(gradez)}
Натиснiть на назву предмету щоб змiнити або видалити оцiнку''',
                             reply_markup=Buttons.configure_grades(message.from_user.id))
    else:
        await message.answer('У вас немає оцiнок з жодного предмету')



@dp.message_handler(state=States.grade)
async def get_grades(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        zno_id = data['zno_id']
        '''checking what we got from state
        because we can get name when we are calling
        state from checking chances'''
        if not zno_id.isdigit():
            zno_id = Controller.get_zno_id(zno_id)
        if validate_grade(message.text):
            data['grade'] = float(message.text)
            await message.answer(Controller.set_grade(
                    message.from_user.id, zno_id, data['grade']),
                    reply_markup=Keyboard.home)
            await state.finish()
        else:
            await message.answer('Невiрне значення. Спробуйте ще раз.')


@dp.message_handler(Text(equals='Додати оцiнки ЗНО', ignore_case=True), state='*')
async def set_grades(message: types.Message, state: FSMContext):
    # checking current state and finish it

    if await state.get_state() is not None:
        await state.finish()
    await message.answer("Оберiть предмет",
                         reply_markup=Buttons.set_grade)


@dp.message_handler(state=States.add_from)
async def additional_zno(message: types.Message, state: FSMContext):
    '''Offering user to add missing grades for speciality '''
    async with state.proxy() as data:
        # checking reply from keyboard
        if message.text == 'Так':
            current_zno = data['subjects'][0]
            await message.answer(f'Введiть оцiнку з {current_zno}')
        elif message.text == 'Нi':
            await message.answer('Повертаємось до головного меню',
                                 reply_markup=Keyboard.home)
            await state.finish()
        # checking for each subject in subject
        else:
            if data['subjects']:
                current_zno = data['subjects'][0]
                zno_id = Controller.get_zno_id(current_zno)
                grade = message.text
                if validate_grade(grade):
                    (Controller.set_grade(message.from_user.id, zno_id, grade))
                    data['subjects'].remove(current_zno)
                    if data['subjects']:
                        await message.answer(f'Введiть оцiнку з {data["subjects"][0]}')
                    else:
                        # change state only when user added all grades
                        info = Controller.get_chances(
                            message.from_user.id,
                            data['region'],
                            data['spec'])
                        await message.answer(
                            result_generation(info),
                            parse_mode=types.ParseMode.MARKDOWN,
                            reply_markup=Keyboard.home)
                        await state.finish()
                else:
                    await message.answer('Невiрне значення,спробуйте ще раз')
            else:
                await message.answer('Всi оцiнки доданi. Спробуйте ще раз',
                                     reply_markup=Keyboard.home)
                await state.finish()


''' Callback handlers'''


@dp.callback_query_handler(state=States.choose_region)
async def choose_area(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['region'] = callback_query.data
    await callback_query.message.edit_text('Зачекайте...')
    areas = Buttons.areas()  # Var for faster edit later
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
    await callback_query.message.edit_text('Рахуємо...')
    info = Controller.get_chances(
        callback_query.from_user.id,
        data['region'],
        data['spec'])
    n = '\n• '
    if info.get('result'):
        if info.get('result') == 'additional':
            await callback_query.message.answer(f'''
На жаль у вас немає оцiнки з одного з додаткових предметiв:
*•{n.join(info['data'])}*{n.split('•')[0]}
Додайте оцiнку в меню та спробуйте ще раз.''',
                                                parse_mode=types.ParseMode.MARKDOWN)
        else:
            await callback_query.message.edit_text(
                result_generation(info),
                parse_mode=types.ParseMode.MARKDOWN)
    else:
        await callback_query.message.answer(
            f'''Нажаль ви не можете вступити за цiєю спецiальнiстю,\
 бо у вас немає оцiнок з:{n}*{n.join(info['data'])}*{n.split('•')[0]}Бажаєте додати їх?''',
            parse_mode=types.ParseMode.MARKDOWN,
            reply_markup=Keyboard.choice)
    async with state.proxy() as data:
        data['subjects'] = info['data']
    await States.add_from.set()
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

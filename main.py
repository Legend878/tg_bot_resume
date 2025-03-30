from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from config import TOKEN
import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup,InlineKeyboardButton, CallbackQuery,ReplyKeyboardRemove, FSInputFile
from fpdf import FPDF
import os
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from datetime import datetime,date
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from email_validator import validate_email, EmailNotValidError
from fpdf import FPDF


PDF_DIRtelegram = "pdf_files"
bot = Bot(TOKEN)
ms = MemoryStorage()
dp = Dispatcher(storage=ms)

# Определение состояний для FSM
class ResumeForm(StatesGroup):
    wait_fio = State()
    wait_age = State()
    wait_country = State()
    wait_city = State()
    wait_gender = State()
    wait_family = State()
    wait_education = State()
    wait_fakyltet = State()
    wait_special = State()
    wait_date_end = State()
    wait_forma = State()
    wait_photo = State()
    wait_email = State()
    wait_phone = State()
    wait_name_job = State()
    wait_type_job = State()
    wait_desire_salary = State()
    wait_graphics_job = State()
    wait_study = State()
    wait_choice = State()
    wait_photo_end = State()


@dp.message(Command('start'))
async def start(message: types.Message):
    main = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Заполнить данные')],
    ], resize_keyboard=True)
    await message.answer("Добро пожаловать! Я могу помочь вам сгенерировать PDF-Резюме.", reply_markup=main)


@dp.message(lambda message: message.text == 'Заполнить данные')
async def fill_data(message: types.Message, state: FSMContext):
    otchestvo_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Нет отчества',callback_data='no_otchestvo')],
    ],)
    await message.answer('Введите ваше ФИО: ',reply_markup=otchestvo_keyboard)
    await state.set_state(ResumeForm.wait_fio)

@dp.callback_query(F.data == 'no_otchestvo')
async def fio_no_otchestvo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(otchestvo='Отсутствует')
    await callback.message.edit_text("Напишите вашу Фамилию и Имя:")  # Меняем текст сообщения
    await callback.answer()  # Завершаем обработку callback

@dp.message(ResumeForm.wait_fio)
async def get_fio(message: types.Message, state: FSMContext):
    data = await state.get_data()
    otchestvo = data.get("otchestvo",None)
    if otchestvo == 'Отсутствует':
        list_fio = message.text.split(' ')
        list_fio = [word.lower().capitalize() for word in list_fio]

        if len(list_fio) == 2:
            surname, name = list_fio
            otchestvo = None
        else:
            await message.answer("Пожалуйста, введите Фамилию и Имя через пробел.")
            return
    else:
        list_fio = message.text.split(' ')
        list_fio = [word.lower().capitalize() for word in list_fio]

        if len(list_fio) == 3:
            surname, name, otchestvo = list_fio
        else:
            await message.answer("Пожалуйста, введите Фамилию, Имя и Отчество через пробел")    
    await state.update_data(surname = surname, name = name, otchestvo = otchestvo)
    await message.answer(f"Фамилия: {surname}\nИмя: {name}\nОтчество: {otchestvo}")

    await message.answer("Введите вашу дату рождения")
    await state.set_state(ResumeForm.wait_age)


# Вычисление возраста
async def calculate_age(year: int,month: int,day: int)->int:
    current_date = datetime.now() 

    age = current_date.year - int(year)

    if(current_date.month, current_date.day) < (int(month),int(day)):
        age -= 1

    return age
   
    

@dp.message(ResumeForm.wait_age)
async def get_age(message: types.Message, state: FSMContext):
    try:
        if '.' in message.text:
            date_birth = message.text.split('.')
        elif '-' in message.text:
            date_birth = message.text.split('-')
        elif ' ' in message.text:
            date_birth = message.text.split(' ')
            
    except Exception as e:
        message.answer('Я не смог распознать даты, пример: 01.01.2000') 
    
    age = await calculate_age(date_birth[-1],date_birth[-2],date_birth[-3])   
    await message.answer(str(age))
    date_birth = '.'.join(date_birth)
    await state.update_data(birth = date_birth )
    await state.update_data(age=age)  # Сохраняем возраст в state_data

    await message.answer("Электронная почта")
    await state.set_state(ResumeForm.wait_email)



def is_valid_email(email: str) -> bool:
    try:
        # Валидация email
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


@dp.message(ResumeForm.wait_email)
async def get_email(message: types.Message, state: FSMContext):
    email = message.text.strip()  # Убираем лишние пробелы

    # Проверяем валидность email
    if not is_valid_email(email):
        await message.answer('Некорректный email. Пожалуйста, введите действительный адрес.')
        return  # Не переходим к следующему состоянию, если email невалиден
    
    await state.update_data(email = email)
    await message.answer('Телефон для связи')
    await state.set_state(ResumeForm.wait_phone)
    
# @dp.message(ResumeForm.wait_other_social_link)
# async def get_other_social_link(message: types.Message, state: FSMContext):
    #   social_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text='Telegram')],
    #     [InlineKeyboardButton(text='VK')],
    #     [InlineKeyboardButton(text='What\'s app')]
    # ])

@dp.message(ResumeForm.wait_phone)
async def get_phone(message: types.Message, state: FSMContext):
    user_phone = message.text

    user_phone = ''.join(filter(str.isdigit, user_phone))
    if len(user_phone) == 11:
        if user_phone[0] == '8':
            user_phone = '+7'+user_phone[1:]
        else:
            user_phone = '+'+user_phone
    elif len(user_phone) == 12 and user_phone[0] =='7':
        user_phone = '+' + user_phone
    else:
        await message.answer('Неккооретный номер телефона')
        return
    await message.answer(f'Ваш номер телефона: {user_phone}')
    try:
        parsed_phone = phonenumbers.parse(user_phone, None)
        if not phonenumbers.is_valid_number(parsed_phone):
            await message.answer('Некорректный номер телефона.')
            return
    except NumberParseException:
        await message.answer('Номер телефона не распознан.')
        return
    
    await state.update_data(phone = user_phone)

    country_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Российская Федерация')],
        [KeyboardButton(text='Беларусь')],
        [KeyboardButton(text='Казахстан')],
        [KeyboardButton(text='Другое')],

    ], resize_keyboard=True)
    await message.answer('Гражданство', reply_markup=country_keyboard)
    await state.set_state(ResumeForm.wait_country)
    


@dp.message(ResumeForm.wait_country)
async def get_country(message: types.Message, state: FSMContext):
    if message.text == 'Другое':
        await message.answer('Введите название вашей страны')
        await state.set_state(ResumeForm.wait_country)
        return  # Прерываем выполнение, чтобы не обновлять состояние 
    await state.update_data(country=message.text)  
    await message.answer("Город проживания",reply_markup=ReplyKeyboardRemove())
    await state.set_state(ResumeForm.wait_city)


@dp.message(ResumeForm.wait_city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)  
    gender_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Мужской')],
        [KeyboardButton(text='Женский')],

    ], resize_keyboard=True)
    await message.answer("Пол",reply_markup=gender_keyboard)
    await state.set_state(ResumeForm.wait_gender)


@dp.message(ResumeForm.wait_gender)
async def get_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text) 
    polojenie_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Холост')],
        [KeyboardButton(text='Женат')],
        [KeyboardButton(text='Не замужем')],
        [KeyboardButton(text='Замужем')],

    ], resize_keyboard=True)
    await message.answer("Семейное положение", reply_markup=polojenie_keyboard)
    await state.set_state(ResumeForm.wait_study)

@dp.message(ResumeForm.wait_study)
async def get_study(message: types.Message, state: FSMContext):
    await state.update_data(family=message.text)  
    study_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Основное общее образование')],
        [KeyboardButton(text='Среднее')],
        [KeyboardButton(text='Среднее специальное')],
        [KeyboardButton(text='Среднее профессиольное')],
        [KeyboardButton(text='Неоконченное высшее')],
        [KeyboardButton(text='Высшее')],
        [KeyboardButton(text='Бакалавр')],
        [KeyboardButton(text='Магистр')],
        [KeyboardButton(text='Кандидат наук')],
        [KeyboardButton(text='Доктор наук')],

    ], resize_keyboard=True)
    await message.answer("Образование", reply_markup=study_keyboard)
    await state.set_state(ResumeForm.wait_name_job)

@dp.message(ResumeForm.wait_name_job)
async def get_name_job(message: types.Message, state: FSMContext):
    await state.update_data(study = message.text)
    name_job_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Не указывать')]
    ], resize_keyboard=True)
    await message.answer("Укажите название желаемой должности",reply_markup=name_job_keyboard)
    await state.set_state(ResumeForm.wait_desire_salary)



@dp.message(ResumeForm.wait_desire_salary)
async def get_name_job(message: types.Message, state: FSMContext):
    if message.text == 'Не указывать':
        await state.update_data(name_job = 'Должность не указана')
    else: 
        await state.update_data(name_job = message.text)

    await message.answer('Укажите желаемую заработанную плату или желаемую вилку в месяц')
    await state.set_state(ResumeForm.wait_type_job)
    


@dp.message(ResumeForm.wait_type_job)
async def get_name_job(message: types.Message, state: FSMContext):
    await state.update_data(salary = message.text)
    type_job_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Полная')],
        [KeyboardButton(text='Частичная')],
        [KeyboardButton(text='Сезонная')],
        [KeyboardButton(text='Проектная')],
        [KeyboardButton(text='Стажировка')],
        [KeyboardButton(text='Волонтёрство')],
        [KeyboardButton(text='Удаленная работа')],
        [KeyboardButton(text='Временная работа')],
    ],resize_keyboard=True)
    await message.answer("Выберите тип занятости",reply_markup=type_job_keyboard)
    await state.set_state(ResumeForm.wait_graphics_job)


@dp.message(ResumeForm.wait_graphics_job)
async def get_name_job(message: types.Message, state: FSMContext):
    await state.update_data(type_job = message.text)
    graphics_job = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Полный день')],
        [KeyboardButton(text='Неполный день')],
        [KeyboardButton(text='Сменный график')],
        [KeyboardButton(text='Гибкий график')],
        [KeyboardButton(text='Ненормированный')],
        [KeyboardButton(text='Вахтовый метод')],
    ], resize_keyboard=True)
    await message.answer("Выберите график работы",reply_markup=graphics_job)
    await state.set_state(ResumeForm.wait_choice)

# ДОБАВЛЯТЬ ПО ЖЕЛАИНЮ ЕСЛИ У ПОЛЬЗОВАТЕЛЯ ЕСТЬ ОБРАЗВАНИЕМ ВЫШЕ


# Обработчик выбора пользователя (добавить образование или опыт работы)
@dp.message(ResumeForm.wait_choice)
async def handle_choice(message: types.Message, state: FSMContext):
    await state.update_data(graphics_job=message.text) 
    # Создаем клавиатуру для выбора
    add_data_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Добавить образование')],
        [KeyboardButton(text='Добавить опыт работы')],
        [KeyboardButton(text='Пропустить')],  
    ], resize_keyboard=True)

    if message.text == 'Добавить образование':
        await message.answer("Введите полное название вашего учебного заведения", reply_markup=ReplyKeyboardRemove())
        await state.set_state(ResumeForm.wait_fakyltet)
    # elif message.text == 'Добавить опыт работы':
    #     await message.answer("Введите название вашей последней должности", reply_markup=ReplyKeyboardRemove())
    #     await state.set_state(ResumeForm.wait_job_title)
    elif message.text == 'Пропустить':
        await message.answer("Вы пропустили добавление образования и опыта работы.")
        # Переходим к следующему шагу (например, запрос фото или завершение)
        await state.set_state(ResumeForm.wait_photo)
    else:
        await message.answer("Пожалуйста, выберите одну из предложенных опций.", reply_markup=add_data_keyboard)

# @dp.message(ResumeForm.wait_education)
# async def get_education(message: types.Message, state: FSMContext):
#     await state.update_data(education=message.text)  # Сохраняем учебное заведение в state_data
#     await message.answer('Образование')
#     await state.set_state(ResumeForm.wait_fakyltet)

@dp.message(ResumeForm.wait_fakyltet)
async def get_education(message: types.Message, state: FSMContext):
    await state.update_data(education=message.text)  
    await message.answer('Факультет')
    await state.set_state(ResumeForm.wait_special)


@dp.message(ResumeForm.wait_special)
async def get_fakyltet(message: types.Message, state: FSMContext):
    await state.update_data(fakyltet=message.text)  
    await message.answer('Специальность')
    await state.set_state(ResumeForm.wait_date_end)


@dp.message(ResumeForm.wait_date_end)
async def get_special(message: types.Message, state: FSMContext):
    await state.update_data(special=message.text)  
    await message.answer('Дата окончания')
    await state.set_state(ResumeForm.wait_forma)


@dp.message(ResumeForm.wait_forma)
async def get_date_end(message: types.Message, state: FSMContext):
    await state.update_data(date_end=message.text)  
    form_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text = 'Очная')],
        [KeyboardButton(text = 'Очно-заочная')],
        [KeyboardButton(text = 'Заочная')],
        [KeyboardButton(text = 'Дистанционная')],
    ])
    await message.answer('Форма обучения', reply_markup=form_keyboard)
    await state.set_state(ResumeForm.wait_photo)


@dp.message(ResumeForm.wait_photo)
async def get_forma(message: types.Message, state: FSMContext):
    await state.update_data(forma=message.text)  
    await message.answer("Прикрепите вашу фотографию",reply_markup=ReplyKeyboardRemove())
    await state.set_state(ResumeForm.wait_photo_end)


@dp.message(lambda message: message.content_type == 'photo', ResumeForm.wait_photo_end)
async def get_photo(message: types.Message, state: FSMContext):
    # Сохраняем фотографию
    photo_id = message.photo[-1].file_id
    photo_file = await bot.get_file(photo_id)
    

    photo_path = f"photos/{message.from_user.id}.jpg"
    
    if not os.path.exists('photos'):
        os.makedirs('photos')
    
    await bot.download_file(photo_file.file_path, destination=photo_path)
    
    # Сохраняем путь к фото в state_data
    await state.update_data(photo=photo_path)


    
    # Получаем все данные из state_data
    state_data = await state.get_data()
    surname = state_data.get('surname','Не указано')
    name = state_data.get('name','Не указано')
    otchstvo = state_data.get('otchestvo','Не указано')

    age = state_data.get('age', 'Не указано')
    birth = state_data.get('birth',' Не указано')
    email = state_data.get('email','не указан')
    phone = state_data.get('phone','не указан')
    country = state_data.get('country', 'Не указано')
    city = state_data.get('city', 'Не указано')
    gender = state_data.get('gender', 'Не указано')
    family = state_data.get('family', 'Не указано')
    study = state_data.get('study','не указано')
    name_job = state_data.get('name_job','Должность не указана')
    salary = state_data.get('salary','не указано')
    type_job = state_data.get('type_job','не указано')
    graphics_job = state_data.get('graphics_job','не указано')
    education = state_data.get('education', 'Не указано')
    fakyltet = state_data.get('fakyltet', 'Не указано')
    special = state_data.get('special', 'Не указано')
    date_end = state_data.get('date_end', 'Не указано')
    forma = state_data.get('forma', 'Не указано')
    # photo_path = state_data.get('photo', 'Фото не загружено')
    
    # Формируем сообщение с собранными данными
    response_message = (
        f"Спасибо {message.from_user.username}! Ваши данные:\n"
        f"Фамилия: {surname}\n"
        f"Имя: {name}\n"
        f"Отчество: {otchstvo}\n"
        f"Дата рождения: {age}\n"
        f"Email: {email}\n"
        f"Телефон: {phone}\n"
        f"Гражданство: {country}\n"
        f"Город проживания: {city}\n"
        f"Пол: {gender}\n"
        f"Семейное положение: {family}\n"
        f"Дата рождения: {birth}\n"
        f"Возраст: {age}\n"
        f"Образование: {study}\n"
        f"Желаемая должность: {name_job}\n"
        f"Заработнная плата: {salary}\n"
        f"Тип: {type_job}\n"
        f"График работы: {graphics_job}\n"
        f"Учебное заведение: {education}\n"
        f"Факультет: {fakyltet}\n"
        f"Специальность: {special}\n"
        f"Дата окончания: {date_end}\n"
        f"Форма обучения: {forma}\n"
        # f"Фото: {photo_path}"
    )

        # Отправляем сообщение с данными пользователю
    await message.answer(response_message,reply_markup=ReplyKeyboardRemove())
    await message.answer_photo(photo_id)      
    # Завершаем состояние FSM
    await state.clear()


    pdf = FPDF()
    pdf.add_page()
    font_path = "pythonProject/PDF FILE/ttf/DejaVuSans.ttf"
    font_path_bold = "pythonProject/PDF FILE/ttf/DejaVuSans-Bold.ttf"  # Путь к жирному шрифту
    pdf.add_font("DejaVuSans", "B", font_path_bold, uni=True)

    pdf.add_font("DejaVuSans", "", font_path, uni=True)
    pdf.set_font("DejaVuSans", size=12)
    # pdf.cell(200, 10, txt="Welcome to Python!", ln=1, align="C")
    full_name = f"{surname} {name} {otchstvo}"

    try:
        # Размещаем фото
        pdf.image(photo_path, x=5, y=10, w=60)  # Фото (x, y, ширина)

        # Устанавливаем начальную позицию для текста
        x_position = 70
        pdf.set_xy(x_position, 10)

        # Имя и должность
        pdf.set_font("DejaVuSans", style='B', size=14)
        pdf.set_x(x_position)

        pdf.cell(0, 10, txt=full_name, ln=True)
        pdf.ln(3)

        pdf.set_font("DejaVuSans", size=12)
        pdf.set_x(x_position)
        pdf.cell(0, 10, txt=name_job, ln=True)

        # Горизонтальная линия
        pdf.set_line_width(0.5)
        pdf.line(x_position, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

        # Желаемая зарплата
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.set_x(x_position)
        pdf.write(10, "Желаемая зарплата: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{salary}")
        pdf.ln(5)

        # Занятость
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.set_x(x_position)
        pdf.write(10, "Занятость: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{type_job}, {graphics_job}")
        pdf.ln(10)

        # Контакты
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.set_x(x_position)
        pdf.write(10, "Контакты: ")
        pdf.ln(5)

        pdf.set_font("DejaVuSans", size=12)
        pdf.set_x(x_position)
        pdf.write(10, f"Телефон: {phone}")
        pdf.ln(5)

        pdf.set_x(x_position)
        pdf.write(10, f"Почта: {email}")  # Исправлено
        pdf.ln(10)

        # Личная информация
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.set_x(x_position)
        pdf.cell(0, 10, txt='Личная информация', ln=True)
        pdf.ln(2)

        # Вертикальная линия
        pdf.set_line_width(0.3)
        pdf.line(x_position - 3, pdf.get_y(), x_position - 3, pdf.get_y() + 40)

        # Гражданство, город, дата рождения, пол, семейное положение
        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Гражданство: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{country}")


        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Город проживания: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{city}")

        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Дата рождения: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{birth} ({age})")

        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Пол: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{gender}")

        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Семейное положение: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{family}")

        pdf.ln(10)




         # Образование
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.set_x(x_position)
        pdf.cell(0, 10, txt='Образование', ln=True)
        pdf.ln(2)

        # Вертикальная линия
        pdf.set_line_width(0.3)
        pdf.line(x_position - 3, pdf.get_y(), x_position - 3, pdf.get_y() + 40)

        # Учебное заведение, Факультет, Специальность, Дата окончания, Форма обучения
        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"{education}")


        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Факультет: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{fakyltet}")

        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Специальность: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{special}")

        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Дата окончания: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{date_end}")

        pdf.ln(7)

        pdf.set_x(x_position)
        pdf.set_font("DejaVuSans", style="B", size=12)
        pdf.write(10, f"Форма обучения: ")
        pdf.set_font("DejaVuSans", size=12)
        pdf.write(10, f"{forma}")

        pdf.ln(7)

        # pdf.set_x(x_position)
        # pdf.set_font("DejaVuSans", style="B", size=12)
        # pdf.write(10, f"Достижения: ")
        # pdf.set_font("DejaVuSans", size=12)
        # pdf.write(10, f"{family}")


    except Exception as e:
        print(f"Произошла ошибка: {e}")

    if not os.path.exists(PDF_DIRtelegram):
        os.makedirs(PDF_DIRtelegram)
    
    pdf_filename = f"{PDF_DIRtelegram}/{message.from_user.id}_resume.pdf"
    pdf.output(pdf_filename)

    pdf_file = FSInputFile(pdf_filename)
    await message.answer_document(pdf_file, caption="Ваше резюме готово!")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')
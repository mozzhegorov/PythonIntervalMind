from collections import namedtuple

from aiogram import Bot, Dispatcher, executor, types
import logging
from models import Poll, Topic, Question, Answer
from sqlalchemy.sql.expression import func
from settings import API_TOKEN
from engine import session
from utils import get_topic_from_db, clear_statistic
from utils import get_data_question
from utils import create_all
from utils import import_from_csv
from utils import save_poll
from utils import get_poll_data
from utils import delete_poll
from utils import save_statistic
from utils import get_statistic_data
from utils import ChatData

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


async def send_quiz(chat_id, quiz_data):
    questions_data = quiz_data["question"]
    question_text = f'{questions_data.id}. {questions_data.text} \n' \
                    f' #{questions_data.topic.name}'
    mediapath = '/home/media/'
    photo = open(mediapath + questions_data.picture, 'rb')
    await bot.send_photo(chat_id=chat_id, photo=photo, caption='hahaha')
    my_quiz = await bot.send_poll(
        chat_id=chat_id,
        question=question_text,
        options=quiz_data['answers'],
        type='quiz',
        correct_option_id=quiz_data['correct_answer_id'],
        is_anonymous=False,
    )
    save_poll(
        my_quiz['poll']['id'],
        my_quiz['poll']['correct_option_id'],
        questions_data.text,
        questions_data.topic.name,
    )


@dp.message_handler(commands=['start', ])
async def send_welcome(message: types.Message):
    """"""
    msg = f'Привет, {message.chat.first_name} {message.chat.last_name}!\n' \
          f'Добро пожаловать в бота MindPyStorm :) \n\n' \
          f'Если ты здесь, значит ты хочешь проверить свои знания по разным темам, будь то ' \
          f'/python или /linux, /docker или /OOP .\n\n' \
          f'Свою статистику можешь глянуть тут же /statistic \n' \
          f'Если ты правильно 3 раза ответил на вопрос, то вопрос больше не будет тебе попадаться \n' \
          f'Так и считает статистика. Закрытая тема = 3 правильных ответа на каждый вопрос. ' \
          f'За неверный ответ минус бал. \n\n' \
          f'В принципе всё просто и понятно. \n' \
          f'Успехов! :)'

    button_python = KeyboardButton('/python')
    button_linux = KeyboardButton('/linux')
    button_git = KeyboardButton('/git')

    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    greet_kb.add(button_python)
    greet_kb.add(button_linux)
    greet_kb.add(button_git)
    await bot.send_message(
        message.chat.id,
        msg,
        reply_markup=greet_kb
    )


@dp.message_handler(commands=['question', ])
async def send_welcome(message: types.Message):
    """"""
    data_for_quiz = get_data_question()
    if False:
        picture = open("pic.png", 'rb')
        await bot.send_photo(message.chat.id, picture)
    await send_quiz(message, data_for_quiz)


@dp.poll_answer_handler()
async def handle_poll_answer(quiz_answer):
    # проверяем ответ
    quiz_answer_data = get_poll_data(quiz_answer['poll_id'])
    topic = quiz_answer_data.topic
    topic_in_database = get_topic_from_db(topic)
    answer_result = save_statistic(quiz_answer_data, quiz_answer)
    if not topic_in_database:
        data_for_quiz = get_data_question()
    else:
        data_for_quiz = get_data_question(topic)
    delete_poll(quiz_answer['poll_id'])
    inline_btn_1 = InlineKeyboardButton(f'Еще вопрос на тему {topic}', callback_data=f'{topic}')
    inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
    await bot.send_message(quiz_answer.user.id, str(answer_result), reply_markup=inline_kb1)

    # my_quiz = await bot.send_poll(
    #     quiz_answer.user.id, 
    #     data_for_quiz['question'].text, 
    #     data_for_quiz['answers'], 
    #     type='quiz',
    #     correct_option_id=data_for_quiz['correct_answer_id'],
    #     is_anonymous=False,
    # )
    # save_poll(
    #     my_quiz['poll']['id'],
    #     my_quiz['poll']['correct_option_id'],
    #     my_quiz['poll']['question'],
    #     topic,
    # )


@dp.message_handler(commands=['initbase', ])
async def init_base(message: types.Message):
    """"""
    message_text = message.text[1:]
    topic_in_database = get_topic_from_db(message_text)
    create_all()
    all_questions, imported_questions = import_from_csv('db/1.csv')
    if not topic_in_database:
        await bot.send_message(
            message.chat.id,
            'База данных обновлена \n'
            f'Из файла прочитано {all_questions} \n'
            f'Импортировано {imported_questions}',
        )


@dp.message_handler(commands=['statistic', ])
async def get_statistic(message: types.Message):
    """"""
    user_statistic = get_statistic_data(message)
    msg = f'Ваша статистика: \n' \
          f'{user_statistic}' \
          f''
    await bot.send_message(
        message.chat.id,
        msg,
    )


@dp.message_handler(commands=['clearstat', ])
async def get_statistic(message: types.Message):
    """"""
    clear_statistic(message)
    msg = f'Ваша статистика очищена'
    await bot.send_message(
        message.chat.id,
        msg,
    )


@dp.message_handler()
async def send_question_message(message: types.Message):
    """"""
    chat = ChatData(
        message.chat.id,
        message.chat.first_name,
        message.chat.last_name,
        message.text[1:],
    )
    await send_question(chat)


@dp.callback_query_handler()
async def send_question_callback(message: types.CallbackQuery):
    """"""
    chat = ChatData(
        message['from'].id,
        message['from'].first_name,
        message['from'].last_name,
        message.data,
    )
    await send_question(chat)


async def send_question(chat_data):
    """"""
    message_text = chat_data.data
    topic_in_database = get_topic_from_db(message_text)
    if not topic_in_database:
        await bot.send_message(
            chat_data.id,
            'Неверная команда',
        )
    else:
        user_name = f'{chat_data.first_name} {chat_data.last_name}'
        data_for_quiz = get_data_question(message_text, user_name)
        if data_for_quiz:
            await send_quiz(chat_data.id, data_for_quiz)
        else:
            await bot.send_message(
                chat_data.id,
                'Эта тема полностью пройдена',
            )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


from aiogram import Bot, Dispatcher, executor, types
import logging
from models import Poll, Topic, Question, Answer
from  sqlalchemy.sql.expression import func
from settings import API_TOKEN
from engine import session
from utils import get_topic_from_db
from utils import get_data_question
from utils import create_all
from utils import import_from_csv
from utils import save_poll
from utils import get_poll_data
from utils import delete_poll
from utils import save_statistic


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def send_quiz(message, quiz_data):
    my_quiz = await bot.send_poll(
        chat_id=message.chat.id,
        question=quiz_data['question'].text,
        options=quiz_data['answers'],
        # options=option_data,
        type='quiz',
        correct_option_id=quiz_data['correct_answer_id'],
        is_anonymous=False,
    )
    message_text = message.text[1:]
    save_poll(
        my_quiz['poll']['id'],
        my_quiz['poll']['correct_option_id'],
        my_quiz['poll']['question'],
        message_text,
    )


@dp.message_handler(commands=['question', ])
async def send_welcome(message: types.Message):
    """"""
    data_for_quiz = get_data_question()
    await send_quiz(message, data_for_quiz)


@dp.poll_answer_handler()
async def handle_poll_answer(quiz_answer):
    # проверяем ответ
    quiz_answer_data = get_poll_data(quiz_answer['poll_id'])
    topic = quiz_answer_data.topic
    topic_in_database = get_topic_from_db(topic)
    save_statistic(quiz_answer_data, quiz_answer)
    if not topic_in_database:
        data_for_quiz = get_data_question()
    else:
        data_for_quiz = get_data_question(topic)
    delete_poll(quiz_answer['poll_id'])
    
        
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
    import_from_csv('db/1.csv')
    if not topic_in_database:
        await bot.send_message(
            message.chat.id, 
            'База данных обновлена', 
        )

@dp.message_handler(commands=['statistic', ])
async def get_statistic(message: types.Message):
    """"""
    message_text = message.text[1:]
    topic_in_database = get_statistic_data(message_text)
    if not topic_in_database:
        await bot.send_message(
            message.chat.id,
            'База данных обновлена',
        )
    
    
@dp.message_handler()
async def add_receipt(message: types.Message):
    """"""
    message_text = message.text[1:]
    topic_in_database = get_topic_from_db(message_text)
    if not topic_in_database:
        await bot.send_message(
            message.chat.id, 
            'Неверная команда', 
        )
    else:
        user_name = f'{message.chat.first_name} {message.chat.last_name}'
        data_for_quiz = get_data_question(message_text, user_name)
        if data_for_quiz:
            await send_quiz(message, data_for_quiz)
        else:
            await bot.send_message(
                message.chat.id, 
                'Эта тема полностью пройдена', 
            )
    
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

from aiogram import Bot, Dispatcher, executor, types
import logging
from models import Topic, Question, Answer
from  sqlalchemy.sql.expression import func
from settings import API_TOKEN
from engine import session
from utils import get_topic_from_db
from utils import get_data_question



# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['question', ])
async def send_welcome(message: types.Message):
    """"""
    data_for_quiz = get_data_question()
    
    await bot.send_poll(
        message.chat.id, 
        data_for_quiz['question'].text, 
        data_for_quiz['answers'], 
        type='quiz',
        correct_option_id=data_for_quiz['correct_answer_id'],
        is_anonymous=False,
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
        data_for_quiz = get_data_question(message_text)
        
        await bot.send_poll(
            message.chat.id, 
            data_for_quiz['question'].text, 
            data_for_quiz['answers'], 
            type='quiz',
            correct_option_id=data_for_quiz['correct_answer_id'],
            is_anonymous=False,
        )
    
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
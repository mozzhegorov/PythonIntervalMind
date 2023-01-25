from random import shuffle
from aiogram import Bot, Dispatcher, executor, types
import logging
from models import Topic, Question, Answer
from  sqlalchemy.sql.expression import func
from settings import API_TOKEN
from engine import session


# API_TOKEN = 

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['вопрос', 'question'])
async def send_welcome(message: types.Message):
    """
    """
    question = session.query(Question).order_by(func.random()).first()
    all_answers = session.query(Answer).filter(Answer.question_id==question.id).all()
    answers = [answer.text for answer in all_answers]
    correct_answer = [num for num, answer in enumerate(all_answers) if answer.correct][0]
    await bot.send_poll(message.chat.id, question.text, 
    answers, 
    type='quiz', correct_option_id=correct_answer, is_anonymous=False)
    
    
@dp.message_handler()
async def add_receipt(message: types.Message):
    """Добавление нового чека"""
    question = session.query(Question).join(Topic).filter(Topic.name==message.text[1:]).order_by(func.random()).first()
    all_answers = session.query(Answer).filter(Answer.question_id==question.id)
    answers = [answer.text for answer in all_answers.all()]
    correct_answer = all_answers.filter(
        Answer.correct==True
        ).first()
    shuffle(answers)
    correct_answer_id = answers.index(correct_answer.text)
    await bot.send_poll(
        message.chat.id, 
        question.text, 
        answers, 
        type='quiz',
        correct_option_id=correct_answer_id,
        is_anonymous=False,
    )
    
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
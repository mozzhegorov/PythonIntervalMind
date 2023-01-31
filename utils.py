from typing import Union
from models import Topic, Question, Answer
from sqlalchemy.sql.expression import func
from engine import session
from random import shuffle


def get_data_question(topic_text: Union[str, None] = None) -> dict:
    question_query = session.query(Question).join(Topic)
    if topic_text:
        question_query = question_query.filter(Topic.name==topic_text)
    random_question = question_query.order_by(func.random()).first()
    all_answers = session.query(Answer).filter(
        Answer.question_id==random_question.id,
        )
    answers = [answer.text for answer in all_answers.all()]
    correct_answer = all_answers.filter(
        Answer.correct==True,
        ).first()
    shuffle(answers)
    correct_answer_id = answers.index(correct_answer.text)
    return {
        'question': random_question,
        'answers': answers,
        'correct_answer_id': correct_answer_id, 
        'correct_answer_id': correct_answer_id, 
    }
    
    
def get_topic_from_db(topic_text: str) -> Union[Topic, None]:
    return session.query(Topic).filter(Topic.name==topic_text).first()
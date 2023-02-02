from typing import Union
from models import Topic
from models import Question
from models import Answer
from models import Poll
from models import Statictic
from sqlalchemy.sql.expression import func
from engine import session
from random import shuffle
import csv
from engine import Base
from engine import engine


def get_data_question(
    topic_text: Union[str, None] = None, 
    user_name: Union[str, None] = None,
    ) -> Union[dict, None]:
    question_query = session.query(Question).join(Topic)
    if topic_text:
        question_query = question_query.filter(Topic.name==topic_text)
    exclude_questions = session.query(Statictic).filter(
        Statictic.user_full_name==user_name, 
        Statictic.correct_cnt>2,
    ).all()
    exit_questions = [question.question_id for question in exclude_questions]
    question_query = question_query.filter(~Question.id.in_(exit_questions))
    random_question = question_query.order_by(func.random()).first()
    if not random_question:
        return None
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



def create_all():
    Base.metadata.create_all(engine)
    
def get_or_create(model, **kwargs):
    """SqlAlchemy implementation of Django's get_or_create.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance, True

def import_from_csv(filename):
    with open(file=filename, mode='r') as file:
        reader = list(csv.reader(file))
        all_questions = 0
        added_questions = 0
        for item in reader[1:]:
            question_from_csv = item[0]
            if not question_from_csv:
                continue
            topic_from_csv = item[1]
            answers_from_csv = item[2:6]
            hint_from_csv = item[6]
            all_questions += 1
            new_topic = get_or_create(Topic, name=topic_from_csv)[0]
            new_question, created = get_or_create(Question, text=question_from_csv, topic_id=new_topic.id)
            if created:
                added_questions += 1
                session.add(new_question)
                session.commit()
                answers = [Answer(correct=False, text=answer, question_id=new_question.id) 
                            for answer in answers_from_csv if answer]
                answers[0].correct = True
                session.bulk_save_objects(answers)
                session.commit()
                
def save_poll(poll_id, correct_answer, question, topic):
    new_poll = Poll(
        id=poll_id, 
        correct_answer=correct_answer, 
        question=question,
        topic=topic,
    )
    session.add(new_poll)
    session.commit()
    
def get_poll_data(poll_id: int) -> Union[Poll, None]:
    return session.query(Poll).filter(Poll.id==poll_id).first()
    
def delete_poll(poll_id: int) -> Union[Poll, None]:
    session.query(Poll).filter(Poll.id==poll_id).delete()
    session.commit()
    
def save_statistic(quiz_answer_data, quiz_anwser):
    topic = get_topic_from_db(quiz_answer_data.topic)
    question = session.query(Question).filter_by(
            text=quiz_answer_data.question,
        ).first()
    answer_result = quiz_answer_data.correct_answer in quiz_anwser['option_ids']
    full_name = f'{quiz_anwser["user"]["first_name"]} {quiz_anwser["user"]["last_name"]}'
    statistic_item, created = get_or_create(
        Statictic, 
        user_full_name=full_name, 
        question_id=question.id,
        topic_id=topic.id,
    )
    statistic_item.correct_cnt += 1 if answer_result else (-1)   
    session.commit()
    print(session.query(Statictic).all())
    
    print(quiz_answer_data, quiz_anwser)
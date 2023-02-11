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


def get_question(topic_text: Union[str, None], user_name: Union[str, None]):
    question_query = session.query(Question).join(Topic)
    if topic_text:
        question_query = question_query.filter(Topic.name == topic_text)
    exclude_questions = session.query(Statictic).filter(
        Statictic.user_full_name == user_name,
        Statictic.correct_cnt > 2,
    ).all()
    exit_questions = [question.question_id for question in exclude_questions]
    question_query = question_query.filter(~Question.id.in_(exit_questions))
    return question_query.order_by(func.random()).first()


def get_answer(question: 'Question'):
    all_answers = session.query(Answer).filter(
        Answer.question_id == question.id,
    )
    answers = [answer.text for answer in all_answers.all()]
    correct_answer = all_answers.filter(
        Answer.correct==True
    ).first()
    shuffle(answers)
    return answers, answers.index(correct_answer.text)


def get_data_question(
        topic_text: Union[str, None] = None,
        user_name: Union[str, None] = None,
) -> Union[dict, None]:
    question = get_question(topic_text, user_name)
    if not question:
        return None
    answers, correct_answer_id = get_answer(question)
    return {
        'question': question,
        'answers': answers,
        'correct_answer_id': correct_answer_id,
    }


def get_topic_from_db(topic_text: str) -> Union[Topic, None]:
    return session.query(Topic).filter(Topic.name == topic_text).first()


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
    return all_questions, added_questions


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
    return session.query(Poll).filter(Poll.id == poll_id).first()


def delete_poll(poll_id: int):
    session.query(Poll).filter(Poll.id == poll_id).delete()
    session.commit()


def save_statistic(quiz_answer_data, quiz_anwser):
    question = session.query(Question).filter_by(
        text=quiz_answer_data.question,
    ).first()
    answer_result = quiz_answer_data.correct_answer in quiz_anwser['option_ids']
    full_name = f'{quiz_anwser["user"]["first_name"]} {quiz_anwser["user"]["last_name"]}'
    statistic_item, created = get_or_create(
        Statictic,
        user_full_name=full_name,
        question_id=question.id,
        topic_id=question.topic.id,
    )
    statistic_item.correct_cnt += 1 if answer_result else (-1)
    session.commit()


def get_statistic_data(message):
    user_name = f'{message.chat.first_name} {message.chat.last_name}'
    all_questions = dict(
        session.query(
            Topic.name,
            func.count(Question.topic_id),
        ).join(
            Topic
        ).group_by(
            Topic
        ).all()
    )

    user_stata = dict(
        session.query(
            Topic.name,
            func.sum(Statictic.correct_cnt),
        ).join(
            Topic
        ).group_by(
            Topic
        ).filter(Statictic.user_full_name == user_name).all()
    )
    result_stata = '\n'.join(
        [f'/{key}:: {value} / {all_questions[key] * 3}'
         for key, value in user_stata.items()]
    )
    return result_stata


def clear_statistic(message):
    user_name = f'{message.chat.first_name} {message.chat.last_name}'
    session.query(Statictic).filter_by(user_full_name=user_name).delete()
    session.commit()

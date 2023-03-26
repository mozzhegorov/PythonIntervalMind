import csv
from dataclasses import dataclass
from random import shuffle
from typing import List, Optional, Tuple, Union

from aiogram.types import Message
from sqlalchemy.sql.expression import func

from engine import Base, engine, session
from models import Answer, Poll, Question, QuizUser, Statistic, Topic


@dataclass
class ChatData:
    id: int
    first_name: str
    last_name: str
    data: str


def get_question(
    topic_text: Optional[str],
    user_name: Optional[str],
) -> QuizUser:
    """
    Получение рандромного вопроса из базы данных по заданной теме,
    которые не прошел пользователь
    """
    question_query = session.query(Question).join(Topic)
    if topic_text:
        question_query = question_query.filter(Topic.name == topic_text)
    exclude_questions = (
        session.query(Statistic)
        .join(QuizUser)
        .filter(
            QuizUser.user_full_name == user_name,
            Statistic.correct_cnt > 2,
        )
        .all()
    )
    exit_questions = [question.question_id for question in exclude_questions]
    question_query = question_query.filter(~Question.id.in_(exit_questions))
    return question_query.order_by(func.random()).first()


def get_answer(question: Question) -> Tuple[List[Answer], int]:
    """
    Получение списка ответов и корректного варианта
    """
    all_answers = session.query(Answer).filter(
        Answer.question_id == question.id,
    )
    answers = [answer.text for answer in all_answers.all()]
    correct_answer = all_answers.filter(Answer.correct == True).first()
    shuffle(answers)
    return answers, answers.index(correct_answer.text)


def get_data_question(
    topic_text: Union[str, None] = None,
    user_name: Union[str, None] = None,
) -> Union[dict, None]:
    """
    Формирование словаря с данными по вопросу
        "question": запись вопроса из БД,
        "answers": список ответов,
        "correct_answer_id": номер правильного ответа
    """
    question = get_question(topic_text, user_name)
    if not question:
        return None
    answers, correct_answer_id = get_answer(question)
    return {
        "question": question,
        "answers": answers,
        "correct_answer_id": correct_answer_id,
    }


def get_topic_from_db(topic_text: str) -> Union[Topic, None]:
    """
    Запись темы из БД согласно фильтру по названию темы
    """
    return session.query(Topic).filter(Topic.name == topic_text).first()


def create_all() -> None:
    """
    Создаем все таблицы БД
    """
    Base.metadata.create_all(engine)


def get_or_create(model, **kwargs):
    """
    Самописный get_or_create для алхимии
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
    """
    Импортим вопросы из файлы в базу данных
    """
    with open(file=filename, mode="r") as file:
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
            new_question, created = get_or_create(
                Question, text=question_from_csv, topic_id=new_topic.id
            )
            if created:
                added_questions += 1
                session.add(new_question)
                session.commit()
                answers = [
                    Answer(
                        correct=False, text=answer, question_id=new_question.id
                    )
                    for answer in answers_from_csv
                    if answer
                ]
                answers[0].correct = True
                session.bulk_save_objects(answers)
                session.commit()
    return all_questions, added_questions


def save_poll(
    poll_id: int,
    correct_answer: int,
    question: Question,
    topic: Topic,
) -> None:
    """
    Сохраняем пол для фиксирования ответов от пользователей.
    Poll - отправленный вопрос.
    После получения ответа от пользователя удаляем запись
    """
    new_poll = Poll(
        id=poll_id,
        correct_answer=correct_answer,
        question=question,
        topic=topic,
    )
    session.add(new_poll)
    session.commit()


def get_poll_data(poll_id: int) -> Union[Poll, None]:
    """
    Получаем запись из БД согласно poll_id
    """
    return session.query(Poll).filter(Poll.id == poll_id).first()


def delete_poll(poll_id: int) -> None:
    """
    Запись Poll запись из БД согласно poll_id
    """
    session.query(Poll).filter(Poll.id == poll_id).delete()
    session.commit()


def save_statistic(quiz_answer_data, quiz_answer) -> None:
    """
    Сохраняем статистику
    TODO: добавить поле user_uuid (id телеграма) и по нему получать пользователя
    """
    question = (
        session.query(Question)
        .filter_by(
            text=quiz_answer_data.question,
        )
        .first()
    )
    answer_result = quiz_answer_data.correct_answer in quiz_answer["option_ids"]
    full_name = f'{quiz_answer["user"]["first_name"]} ' \
                f'{quiz_answer["user"]["last_name"]}'
    user, created = get_or_create(
        QuizUser,
        user_full_name=full_name,
    )
    statistic_item, created = get_or_create(
        Statistic,
        user=user,
        question_id=question.id,
        topic_id=question.topic.id,
    )
    statistic_item.correct_cnt += 1 if answer_result else (-1)
    session.commit()


def get_statistic_string(message: Message) -> str:
    """
    Получение текста о статистике
    """
    user_name = f"{message.chat.first_name} {message.chat.last_name}"
    all_questions = dict(
        session.query(
            Topic.name,
            func.count(Question.topic_id),
        )
        .join(Topic)
        .group_by(Topic)
        .all()
    )

    user_stata = dict(
        session.query(
            Topic.name,
            func.sum(Statistic.correct_cnt),
        )
        .join(Topic)
        .join(QuizUser)
        .group_by(Topic)
        .filter(QuizUser.user_full_name == user_name)
        .all()
    )
    result_stata = "\n".join(
        [
            f"/{key}:: {value} / {all_questions[key] * 3}"
            for key, value in user_stata.items()
        ]
    )
    return result_stata


def clear_statistic(message: Message) -> None:
    """
    Очистка статистики согласно юзера
    TODO: изменить фильтрацию юзера согласно айди телеграма
    """
    user_name = f"{message.chat.first_name} {message.chat.last_name}"
    user = (
        session.query(QuizUser)
        .filter(QuizUser.user_full_name == user_name)
        .first()
    )
    session.query(Statistic).filter(Statistic.user_id == user.id).delete()
    session.commit()

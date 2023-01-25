
from sqlalchemy import Column, Float, Boolean, create_engine, ForeignKey, Table, and_, not_, func, event
from sqlalchemy import (Integer,
                        String,
                        DateTime,
                        )
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import (declarative_base,
                            relationship, sessionmaker, validates,
                            )
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.exc import NoResultFound
from engine import Base
from engine import engine
from engine import Session
from engine import session
import csv

class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True)
    text = Column(String(128), nullable=False)
    topic_id = Column(Integer, ForeignKey('topic.id'))
    topic = relationship(
        "Topic",
        back_populates="questions",
        lazy="select", 
    )
    answers = relationship(
        "Answer",
        back_populates="question",
        lazy="subquery", 
    )

    def __repr__(self):
        return f"Question(id={self.id!r}, " \
               f"text={self.text!r})"

    def to_json(self):
        return {item.name: getattr(self, item.name) for item in self.__table__.columns}
    

class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    questions = relationship(
        "Question",
        back_populates="topic",
        lazy="subquery", 
    )

    def __repr__(self):
        return f"Topic(id={self.id!r}, name={self.name!r})"
    

class Answer(Base):
    __tablename__ = "answer"

    id = Column(Integer, primary_key=True)
    text = Column(String(64), nullable=False)
    correct = Column(Boolean, nullable=False)
    question_id = Column(Integer, ForeignKey('question.id'))
    question = relationship(
        "Question",
        back_populates="answers",
        lazy="subquery", 
    )

    def __repr__(self):
        return f"Answer(id={self.id!r}, text={self.text!r})"

    def to_json(self):
        return {item.name: getattr(self, item.name) for item in self.__table__.columns}


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
        for item in reader[1:]:
            question_from_csv = item[0]
            topic_from_csv = item[1]
            answers_from_csv = item[2:5]
            hint_from_csv = item[6]
            new_topic = get_or_create(Topic, name=topic_from_csv)[0]
            new_question, created = get_or_create(Question, text=question_from_csv, topic_id=new_topic.id)
            if created:
                session.add(new_question)
                session.commit()
                answers = [Answer(correct=False, text=answer, question_id=new_question.id) 
                            for answer in answers_from_csv]
                answers[0].correct = True
                session.bulk_save_objects(answers)
                session.commit()
        



from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from engine import Base


class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True)
    text = Column(String(256), nullable=False)
    picture = Column(String(100), nullable=True)
    topic_id = Column(Integer, ForeignKey("topic.id"))
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
        return f"Question(id={self.id!r}, " f"text={self.text!r})"

    def to_json(self):
        return {
            item.name: getattr(self, item.name)
            for item in self.__table__.columns
        }


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
    question_id = Column(Integer, ForeignKey("question.id"))
    question = relationship(
        "Question",
        back_populates="answers",
        lazy="subquery",
    )

    def __repr__(self):
        return f"Answer(id={self.id!r}, text={self.text!r})"

    def to_json(self):
        return {
            item.name: getattr(self, item.name)
            for item in self.__table__.columns
        }


class Poll(Base):
    __tablename__ = "poll"

    id = Column(Integer, primary_key=True)
    question = Column(String(256), nullable=False)
    topic = Column(String(64), nullable=False)
    correct_answer = Column(Integer, nullable=False)

    def __repr__(self):
        return f"Poll(id={self.id!r}, question={self.question!r})"


class Statistic(Base):
    __tablename__ = "statistic"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("quizuser.id"))
    user = relationship(
        "QuizUser",
        lazy="subquery",
    )

    question_id = Column(Integer, ForeignKey("question.id"))
    question = relationship(
        "Question",
        lazy="subquery",
    )
    topic_id = Column(Integer, ForeignKey("topic.id"))
    topic = relationship(
        "Topic",
        lazy="select",
    )
    correct_cnt = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"user_full_name(id={self.user.user_full_name!r}, question={self.question!r}), correct_cnt={self.correct_cnt!r})"


class QuizUser(Base):
    __tablename__ = "quizuser"

    id = Column(Integer, primary_key=True)
    user_full_name = Column(String(64), nullable=False)
    statistic = relationship(
        "Statistic",
        back_populates="user",
        lazy="subquery",
    )

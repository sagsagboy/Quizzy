# coding: utf-8
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = 'users'

    ID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(Text)
    Passhash = Column(Text)
    Salt = Column(Text)
    sessionHash = Column(Text)


class Game(Base):
    __tablename__ = 'Games'

    ID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(Text)
    OwnerID = Column(ForeignKey('users.ID'))

    user = relationship('User')


class GameRun(Base):
    __tablename__ = 'GameRuns'

    ID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(Text)
    CurrQustion = Column(Text)
    Status = Column(Text)
    StartTime = Column(Text)
    gameID = Column(ForeignKey('Games.OwnerID'))
    gamePin = Column(Text)
    nextQTime = Column(Text)

    Game = relationship('Game')


class Question(Base):
    __tablename__ = 'questions'
    __table_args__ = (
        CheckConstraint('RightAnswer <= 4 AND RightAnswer > 0), "order" TEXT, gameID TEXT REFERENCES Games (ID)'),
    )

    ID = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text)
    option1 = Column(Text)
    option2 = Column(Text)
    option3 = Column(Text)
    option4 = Column(Text)
    image = Column(Text)
    RightAnswer = Column(Integer)
    order = Column(Text)
    gameID = Column(ForeignKey('Games.ID'))

    Game = relationship('Game')


t_userAnswers = Table(
    'userAnswers', metadata,
    Column('userID', ForeignKey('users.ID')),
    Column('questionID', ForeignKey('questions.ID')),
    Column('gameRunsID', ForeignKey('GameRuns.ID')),
    Column('time', Integer),
    Column('answer', Integer),
    Column('IsCorrect', Boolean),
    CheckConstraint('answer <= 4 and answer > 0), IsCorrect BOOLEAN')
)


t_userScore = Table(
    'userScore', metadata,
    Column('userID', ForeignKey('users.ID')),
    Column('gameRunsID', ForeignKey('GameRuns.ID')),
    Column('score', Integer)
)

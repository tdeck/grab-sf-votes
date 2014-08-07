"""
Definitions for ORM models and SQLite setup.
    - Troy Deck (troy.deque@gmail.com)
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer, String, Date, Boolean
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine

CONNECTION_STRING = 'sqlite:///vote_db.sqlite'

Base = declarative_base()

class Legislator(Base):
    __tablename__ = 'Legislators'

    id = Column(Integer, primary_key=True)
    name =  Column(String(255))

    votes = relationship('Vote', backref='legislator')

    def __init__(self, name):
        self.name = name

class Proposal(Base):
    __tablename__ = 'Proposals'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    file_number = Column(Integer)
    status = Column(String(255))
    introduction_date = Column(Date)
    proposal_type = Column(String(255))

    vote_events = relationship('VoteEvent', backref='proposal')

    def __init__(self, file_number, title):
        self.file_number = file_number
        self.title = title

class VoteEvent(Base):
    __tablename__ = 'VoteEvents'

    id = Column(Integer, primary_key=True)
    vote_date = Column(Date)
    proposal_id = Column(Integer, ForeignKey('Proposals.id'))

    votes = relationship('Vote', backref='vote_event')

    def __init__(self, proposal, vote_date):
        self.proposal = proposal
        self.vote_date = vote_date

class Vote(Base):
    __tablename__ = 'Votes'
    
    legislator_id = Column(Integer, ForeignKey('Legislators.id'), primary_key=True)
    vote_event_id = Column(Integer, ForeignKey('VoteEvents.id'), primary_key=True)
    aye_vote = Column(Boolean)

    def __init__(self, legislator, proposal, aye):
        self.legislator = legislator
        self.proposal = proposal
        self.aye_vote = aye

engine = create_engine(CONNECTION_STRING)
session = sessionmaker(bind=engine)()

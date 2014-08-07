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
    """
    A supervisor with a name.
    """
    __tablename__ = 'legislators'

    id = Column(Integer, primary_key=True)
    name =  Column(String(255))

    votes = relationship('Vote', backref='legislator')

    def __init__(self, name):
        self.name = name

class Proposal(Base):
    """
    A piece of legislation (law, ordinance, whatever), passed or not.
    """
    __tablename__ = 'proposals'

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
    """
    A time when a vote was held about a piece of proposed legislation.
    """
    __tablename__ = 'vote_events'

    id = Column(Integer, primary_key=True)
    vote_date = Column(Date)
    proposal_id = Column(Integer, ForeignKey('proposals.id'))

    votes = relationship('Vote', backref='vote_event')

    def __init__(self, proposal, vote_date):
        self.proposal = proposal
        self.vote_date = vote_date

class Vote(Base):
    """
    A particular legislator's vote during a vote event.
    NOTE: If there is no vote here, the legislator may have been absent or 
          may have abstained.
    """
    __tablename__ = 'votes'
    
    legislator_id = Column(Integer, ForeignKey('legislators.id'), primary_key=True)
    vote_event_id = Column(Integer, ForeignKey('vote_events.id'), primary_key=True)
    aye_vote = Column(Boolean)

    def __init__(self, legislator, proposal, aye):
        self.legislator = legislator
        self.proposal = proposal
        self.aye_vote = aye

engine = create_engine(CONNECTION_STRING)
session = sessionmaker(bind=engine)()

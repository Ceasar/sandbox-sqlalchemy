"""
Demonstrate how to filter_by custom comparators.
"""
from sqlalchemy import Column, Integer, String, create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.sql import or_


engine = create_engine('sqlite:///:memory:')
Base = declarative_base()
Session = orm.sessionmaker(engine)


class Either(Comparator):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __eq__(self, other):
        return or_(other == self.left, other == self.right)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(64))
    alias = Column(String(64))

    @hybrid_property
    def name(self):
        return self.alias or self.first_name

    @name.comparator
    def name(self):
        return Either(self.first_name, self.alias)

    def __repr__(self):
        return 'User("{}" a.k.a. "{}")'.format(self.first_name, self.alias)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    session = Session()

    user = User(first_name="Edward", alias="Ed")
    session.add(user)
    session.flush()

    q1 = session.query(User).filter_by(name="Edward")
    print q1
    print q1.one()

    q2 = session.query(User).filter_by(name="Ed")
    print '-' * 80
    print q2
    print q2.one()

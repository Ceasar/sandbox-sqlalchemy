"""
This module demonstrates a circumstance in which SQLAlchemy generates a warning
because the user manipulates the session during the "execute" portion of the
flush [1]_::

    /lib/python2.7/site-packages/sqlalchemy/orm/session.py:1471:
        SAWarning: Usage of the 'Session.add()' operation is not currently
        supported within the execution stage of the flush process. Results may
        not be consistent.  Consider using alternative event listeners or
        connection-level operations instead.
        self._flush_warning("Session.add()")

In this case, the warning is generated by the initialization of an object that
has a column with a default value where an event logger looking for 'set'
events on that column adds an object to the session.

This can be fixed in a number of ways, including using a different session from
the one flushing the User.

.. [1]
    http://docs.sqlalchemy.org/en/rel_0_8/changelog/changelog_08.html

"""
from sqlalchemy import Column, Integer, String, create_engine, event, orm
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('sqlite:///:memory:')
Base = declarative_base()
Session = orm.sessionmaker(engine)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), default="John")


class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)


def main():
    session = Session()

    @event.listens_for(User.name, 'set')
    def listener(target, value, oldvalue, initiator):
        session.add(Event())
        session.commit()

    user = User()
    session.add(user)
    session.flush()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    main()
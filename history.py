"""
What causes orm.attributes.History [2]_ to be populated?

Accessing an attribute causes a SELECT statement to be emitted, loading every
attribute of an object::

    SELECT user.id AS user_id, \
            user.scalar AS user_scalar, \
            user.nullable AS user_nullable, \
            user.nullable_default AS user_nullable_default

Many of the results of these tests can be deduced from the source. [1]_ In
particular, look at History.from_scalar_attribute,
History.from_object_attribute, and History.from_collection.

.. [1] https://github.com/zzzeek/sqlalchemy/blob/master/lib/sqlalchemy/orm/attributes.py
.. [2] http://docs.sqlalchemy.org/en/rel_0_9/orm/session.html#sqlalchemy.orm.attributes.History

"""
import logging

import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, orm
from sqlalchemy.ext.declarative import declarative_base

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


engine = create_engine('sqlite:///:memory:')
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    scalar = Column(String(64))
    nullable = Column(String(64), nullable=True)
    nullable_default = Column(String(64), nullable=True, default="Charlie")

    parent_id = Column(Integer, ForeignKey('user.id'))
    children = orm.relationship('User', uselist=True)


Base.metadata.create_all(engine)
Session = orm.sessionmaker(engine)


def test_history_scalar_nothing():
    user = User()
    history = orm.attributes.get_history(user, "scalar")
    assert history == ((), (), ())


def test_history_vector_nothing():
    user = User()
    history = orm.attributes.get_history(user, "children")
    assert history == ((), [], ())


def test_history_scalar_accessed():
    user = User()
    user.scalar
    history = orm.attributes.get_history(user, "scalar")
    assert history == ((), [None], ())


def test_history_vector_accessed():
    user = User()
    user.children
    history = orm.attributes.get_history(user, "children")
    assert history == ((), [], ())


def test_history_scalar_set():
    user = User()
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Alice'], (), ())


def test_history_vector_added():
    user1, user2 = User(), User()
    user1.children.append(user2)
    history = orm.attributes.get_history(user1, "children")
    assert history == ([user2], [], [])


def test_history_scalar_accessed_and_set():
    user = User()
    user.scalar
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Alice'], (), [None])


def test_history_scalar_set_twice():
    user = User()
    user.scalar = "Alice"
    user.scalar = "Bob"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Bob'], (), ())


def test_history_scalar_accessed_and_set_twice():
    user = User()
    user.scalar
    user.scalar = "Alice"
    user.scalar = "Bob"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Bob'], (), [None])


def test_history_after_flush():
    user = User()
    user.scalar = "Alice"
    session = Session()
    session.add(user)
    session.flush()
    history = orm.attributes.get_history(user, "scalar")
    assert history == ((), ['Alice'], ())


def test_history_vector_after_flush():
    user1, user2 = User(), User()
    user1.children.append(user2)
    session = Session()
    session.add(user1)
    session.flush()
    history = orm.attributes.get_history(user1, "children")
    assert history == ((), [user2], ())


def test_history_vector_remove_after_flush():
    user1, user2 = User(), User()
    user1.children.append(user2)
    session = Session()
    session.add(user1)
    session.flush()
    user1.children.remove(user2)
    history = orm.attributes.get_history(user1, "children")
    assert history == ([], [], [user2])


def test_history_after_commit():
    session = Session()
    user = User()
    user.scalar = "Alice"
    session.add(user)
    session.commit()
    history = orm.attributes.get_history(user, "scalar")
    assert history == ((), ['Alice'], ())


def test_history_set_after_flush():
    session = Session()
    user = User()
    user.scalar = "Alice"
    session.add(user)
    session.flush()
    user.scalar = "Bob"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Bob'], (), ['Alice'])


def test_history_set_to_same_after_flush():
    session = Session()
    user = User()
    user.scalar = "Alice"
    session.add(user)
    session.flush()
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar")
    assert history == ((), ['Alice'], ())


def test_history_nullable_after_flush_and_set():
    """
    Flushing an object with a nullable column does not cause None to be set,
    therefore nothing appears in History.deleted.
    """
    session = Session()
    user = User()
    session.add(user)
    session.flush()
    user.nullable = "Bob"
    history = orm.attributes.get_history(user, "nullable")
    assert history == (['Bob'], (), ())


def test_history_del_nullable_after_flush():
    """
    Flushing an object with a nullable column does not cause None to be set,
    therefore nothing appears in History.deleted.
    """
    session = Session()
    user = User()
    user.nullable = "Bob"
    session.add(user)
    session.flush()
    del user.nullable
    history = orm.attributes.get_history(user, "nullable")
    assert history == ((), (), ['Bob'])


def test_history_nullable_default_after_flush_and_set():
    """
    Flushing an object with a column with a default value causes it to be set,
    therefore it appears in History.deleted.
    """
    session = Session()
    user = User()
    session.add(user)
    session.flush()
    user.nullable_default = "Bob"
    history = orm.attributes.get_history(user, "nullable_default")
    assert history == (['Bob'], (), ["Charlie"])


def test_history_after_commit_and_set():
    session = Session()
    user = User()
    user.scalar
    user.scalar = "Alice"
    session.add(user)
    session.commit()
    user.scalar = "Bob"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Bob'], (), ())


def test_history_after_commit_access_and_set():
    session = Session()
    user = User()
    user.scalar
    user.scalar = "Alice"
    session.add(user)
    session.commit()
    user.scalar
    user.scalar = "Bob"
    history = orm.attributes.get_history(user, "scalar")
    assert history == (['Bob'], (), (['Alice']))


def test_history_with_value():
    session = Session()
    user = User(scalar="Bob")
    session.add(user)
    session.flush()
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar")
    assert history.deleted == ["Bob"]


def test_history_default():
    session = Session()
    user = User()
    session.add(user)
    session.flush()
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar")
    assert history.deleted == ()


def test_history_default2():
    session = Session()
    user = User()
    session.add(user)
    session.flush()
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar",
                                         orm.attributes.PASSIVE_NO_INITIALIZE)
    assert history.deleted == ()


def test_history_default_with_value():
    session = Session()
    user = User(nullable_default="Bob")
    session.add(user)
    session.flush()
    user.scalar = "Alice"
    history = orm.attributes.get_history(user, "scalar")
    assert history.deleted == ()


def test_history_nullable_unset():
    session = Session()
    user = User()
    session.add(user)
    session.flush()
    user.nullable = "Alice"
    history = orm.attributes.get_history(user, "nullable")
    assert history.deleted == ()


def test_history_nullable_accessed():
    session = Session()
    user = User()
    user.nullable
    session.add(user)
    session.flush()
    user.nullable = "Alice"
    history = orm.attributes.get_history(user, "nullable")
    assert history.deleted == [None]


def test_history_set_to_none():
    """
    Setting the value of a nullable column to None causes History.deleted to
    populate.
    """
    session = Session()
    user = User(nullable="Bob")
    session.add(user)
    session.flush()
    user.nullable = "Alice"
    history = orm.attributes.get_history(user, "nullable")
    assert history.deleted == ["Bob"]


def test_history_deleted_is_set_in_listener():
    session = Session()

    @sqlalchemy.event.listens_for(session, 'before_flush')
    def before_flush(session, *args):
        for target in session.dirty:
            history = orm.attributes.get_history(user, "nullable")
            assert history.deleted == ()

    user = User()
    session.add(user)
    session.flush()
    user.nullable = "Alice"

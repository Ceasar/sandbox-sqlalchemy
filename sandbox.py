"""
Demonstrates how the session works and how to catch update events.
"""
import sqlalchemy
from sqlalchemy import (MetaData, Table, Column, ForeignKey, Integer, String,
                        create_engine, orm)

metadata = MetaData()

user_table = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(40)),
)

address_table = Table(
    'address',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('value', String(40)),
    Column('user_id', Integer, ForeignKey('user.id')),
)


event_table = Table(
    'event',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('attribute', String(64)),
    Column('old_value', String(64)),
    Column('new_value', String(64)),
)


class User(object):
    pass


class Address(object):
    pass


class Event(object):
    pass

orm.mapper(User, user_table, properties={
    'address': orm.relationship(Address, backref='user', uselist=False)
})
orm.mapper(Address, address_table, properties={
})
orm.mapper(Event, event_table, properties={
})


def print_session(session):
    """
    Print the state of the session.
    """
    print '-' * 80
    print 'session:', session
    print 'dirty:', session.dirty
    print 'identity_map:', session.identity_map
    for instance in session.identity_map.values():
        print
        if isinstance(instance, User):
            print "name:", getattr(instance, 'name')
            print "name:", orm.attributes.get_history(instance, 'name')
        if isinstance(instance, Address):
            print "userid:", orm.attributes.get_history(instance, 'user_id')
            print "value:", orm.attributes.get_history(instance, 'value')
    print

if __name__ == "__main__":
    engine = create_engine('sqlite:///sandbox.db')
    metadata.create_all(engine)
    Session = orm.sessionmaker(engine)
    s = Session()
    q = s.query(User)

    @sqlalchemy.event.listens_for(User, 'before_update')
    def before_update(mapper, connection, target):
        print "before update\n" + '-' * 80
        if s.is_modified(target):
            print "modified"
        print "name:", orm.attributes.get_history(target, 'name')
        print

    @sqlalchemy.event.listens_for(s, 'before_flush')
    def before_flush(session, *args):
        print "before flush"
        print_session(session)

    @sqlalchemy.event.listens_for(s, 'after_flush')
    def after_flush(session, *args):
        print "after flush"
        print_session(session)

    @sqlalchemy.event.listens_for(s, 'after_flush_postexec')
    def after_flush_postexec(session, *args):
        print "after flush postexec"
        print_session(session)

    @sqlalchemy.event.listens_for(s, 'before_commit')
    def before_commit(session, *args):
        print "before_commit"
        print_session(session)

    @sqlalchemy.event.listens_for(s, 'after_commit')
    def after_commit(session, *args):
        print "after_commit"
        print_session(session)

    user = q.get(1)
    address = s.query(Address).get(1)
    # Create a user if one does not yet exist
    if not user:
        user = User()
        address = Address()
        address.value = '123 Bakers Lane'
    user.name = "John Doe"
    address.user_id = user.id

    s.add(user)
    s.add(address)
    s.commit()

    print '=' * 80
    s.expunge(user)
    # NOTE: commenting out this line causes 'deleted' to not be populated
    user = q.get(1)
    user.name = "Jane Doe"
    s.add(user)
    s.commit()

"""
    print '=' * 80
    user.name = "Jane Doe"
    s.commit()
"""

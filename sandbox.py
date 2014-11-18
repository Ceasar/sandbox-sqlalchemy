from sqlalchemy import (MetaData, Table, Column, ForeignKey, Integer, String,
                        create_engine, orm)
metadata = MetaData()

user_table = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(40)),
    Column('age', Integer),
    Column('password', String),
)

address_table = Table(
    'address',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('value', String(40)),
    Column('user_id', Integer, ForeignKey('user.id')),
)


class User(object):
    pass


class Address(object):
    pass

orm.mapper(User, user_table, properties={
    'related': orm.relationship(Address)
})
orm.mapper(Address, address_table, properties={
})

if __name__ == "__main__":
    engine = create_engine('sqlite:///sandbox.db')
    metadata.create_all(engine)
    session = orm.Session(engine)
    q = session.query(User)

    # Create a user if one does not yet exist
    if not q.all():
        u = User()
        u.name = "John Doe"
        u.age = 21
        u.password = "secret"
        session.add(u)
        session.commit()

import datetime
import sqlalchemy
import sqlalchemy.orm as orm
from .db import SqlAlchemyBase


class PostFile(SqlAlchemyBase):
    __tablename__ = 'post_files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    post_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('posts.id'), nullable=False)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('files.id'), nullable=False)
    order = sqlalchemy.Column(sqlalchemy.Integer, default=0)


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User', back_populates='posts')
    post_files = orm.relationship('PostFile', backref='post', order_by=PostFile.order)

    @property
    def files(self):
        return [pf.file for pf in self.post_files]

    def __repr__(self):
        return f'{self.id} | {self.title} | user:{self.user_id}'

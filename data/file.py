import zlib
import datetime
import sqlalchemy
import sqlalchemy.orm as orm
from .db import SqlAlchemyBase


class File(SqlAlchemyBase):
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, default='main.py')
    code_compressed = sqlalchemy.Column(sqlalchemy.LargeBinary, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User', back_populates='files')
    post_files = orm.relationship('PostFile', backref='file')

    def set_code(self, code: str):
        self.code_compressed = zlib.compress(code.encode('utf-8'), level=6)

    def get_code(self) -> str:
        if not self.code_compressed:
            return ''
        return zlib.decompress(self.code_compressed).decode('utf-8')

    def __repr__(self):
        return f'{self.id} | {self.name} | user:{self.user_id}'

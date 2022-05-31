#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : baseModel.py
# @Software: PyCharm
from datetime import datetime
from werkzeug.exceptions import abort

from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy, BaseQuery, Pagination
from sqlalchemy import MetaData
from contextlib import contextmanager

from config.config import conf
from .utils.jsonUtil import JsonUtil


class SQLAlchemy(_SQLAlchemy):
    """ 自定义SQLAlchemy并继承SQLAlchemy """

    @contextmanager
    def auto_commit(self):
        """ 自定义上下文处理数据提交和异常回滚 """
        try:
            yield
            self.session.commit()  # 提交到数据库，修改数据
        except Exception as error:
            db.session.rollback()  # 事务如果发生异常，执行回滚
            raise error

    def execute_query_sql(self, sql):
        """ 执行原生查询sql，并返回字典 """
        res = self.session.execute(sql).fetchall()
        return dict(res) if res else {}


class Qeury(BaseQuery):
    """ 重写query方法，使其默认加上status=0 """

    def filter_by(self, **kwargs):
        """ 如果传过来的参数中不含is_delete，则默认加一个is_delete参数，状态为0 查询有效的数据"""
        # kwargs.setdefault('is_delete', 0)
        return super(Qeury, self).filter_by(**kwargs)

    def paginate(self, page=1, per_page=20, error_out=True, max_per_page=None):
        """ 重写分页器，把页码和页数强制转成int，解决服务器吧int识别为str导致分页报错的问题"""
        page, per_page = int(page) or conf['page']['pageNum'], int(per_page) or conf['page']['pageSize']
        if max_per_page is not None:
            per_page = min(per_page, max_per_page)
        items = self.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)
        total = self.order_by(None).count()
        return Pagination(self, page, per_page, total, items)


# 由于数据库迁移的时候，不兼容约束关系的迁移，下面是百度出的解决方案
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(
    query_class=Qeury,  # 指定使用修改过后的Qeury
    metadata=MetaData(naming_convention=naming_convention),
    use_native_unicode='utf8')


class BaseModel(db.Model, JsonUtil):
    """ 基类模型 """
    __abstract__ = True

    # is_delete = db.Column(db.SmallInteger, default=0, comment='通过更改状态来判断记录是否被删除, 0数据有效, 1数据已删除')
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    created_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='修改时间')
    create_user = db.Column(db.Integer(), nullable=True, default=1, comment='创建数据的用户id')
    update_user = db.Column(db.Integer(), nullable=True, default=1, comment='修改数据的用户id')

    @property
    def str_created_time(self):
        return datetime.strftime(self.created_time, "%Y-%m-%d %H:%M:%S")

    @property
    def str_update_time(self):
        return datetime.strftime(self.update_time, "%Y-%m-%d %H:%M:%S")

    def create(self, attrs_dict: dict, *args):
        """ 插入数据，若指定了字段，则把该字段的值转为json """
        with db.auto_commit():
            for key, value in attrs_dict.items():
                if hasattr(self, key) and key != 'id':
                    setattr(self, key, self.dumps(value) if key in args else value)

            # 如果是执行初始化脚本，获取不到current_user，try一下
            try:
                setattr(self, 'create_user', current_user.id)
                setattr(self, 'update_user', current_user.id)
            except Exception as error:
                pass
            db.session.add(self)
        return self

    def update(self, attrs_dict: dict, *args):
        """ 修改数据，若指定了字段，则把该字段的值转为json """
        # 如果是执行初始化脚本，获取不到current_user，try一下
        with db.auto_commit():
            for key, value in attrs_dict.items():
                if hasattr(self, key) and key not in ['id', 'num']:
                    setattr(self, key, self.dumps(value) if key in args else value)
            try:
                setattr(self, 'update_user', current_user.id)
            except Exception as error:
                pass

    def insert_or_update(self, attrs_dict: dict, *args, **kwargs):
        """ 创建或更新 """
        old_data = self.get_first(**kwargs)
        if old_data:
            old_data.update(attrs_dict, *args)
            return old_data
        return self.create(attrs_dict, *args)

    def delete(self):
        """ 删除单条数据 """
        with db.auto_commit():
            db.session.delete(self)

    # def delete(self):
    #     """ 软删除 """
    #     self.is_delete = 1

    def is_create_user(self, user_id):
        """ 判断当前传进来的id为数据创建者 """
        return self.create_user == user_id

    @classmethod
    def get_first(cls, **kwargs):
        """ 获取第一条数据 """
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        """ 获取全部数据 """
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_filter_by(cls, **kwargs):
        """ 获取filter_by对象 """
        return cls.query.filter_by(**kwargs)

    @classmethod
    def get_filter(cls, **kwargs):
        """ 获取filter对象 """
        return cls.query.filter(**kwargs)

    @classmethod
    def change_sort(cls, id_list, page_num, page_size):
        """ 批量修改排序 """
        with db.auto_commit():
            for index, data_id in enumerate(id_list):
                cls.get_first(id=data_id).num = (page_num - 1) * page_size + index

    @classmethod
    def get_max_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 """
        max_num_data = cls.get_filter_by(**kwargs).order_by(cls.num.desc()).first()
        return max_num_data.num if max_num_data else 0

    @classmethod
    def get_insert_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 + 1 """
        return cls.get_max_num(**kwargs) + 1

    def to_dict(self, to_dict: list = [], pop_list: list = []):
        """ 自定义序列化器，把模型的每个字段转为key，方便返回给前端 """
        dict_data = {}
        for column in self.__table__.columns:
            if column.name not in pop_list:
                if column.name == 'created_time':
                    dict_data['created_time'] = self.str_created_time
                elif column.name == 'update_time':
                    dict_data['update_time'] = self.str_update_time
                else:
                    data = getattr(self, column.name)
                    # 字段在要转json的列表里面，且字段有值，就转为json
                    dict_data[column.name] = data if column.name not in to_dict or not data else self.loads(data)
        return dict_data

    @classmethod
    def pagination(cls, page_num, page_size, filters: list = [], order_by=None):
        """ 分页, 如果没有传页码和页数，则根据查询条件获取全部数据
        filters：过滤条件
        page_num：页数
        page_size：页码
        order_by: 排序规则
        """
        if page_num and page_size:
            query_obj = cls.query.filter(*filters).order_by(order_by) if filters else cls.query.order_by(order_by)
            result = query_obj.paginate(page_num, per_page=page_size, error_out=False)
            return {"total": result.total, "data": [model.to_dict() for model in result.items]}
        all_data = cls.query.filter(*filters).order_by(order_by).all()
        return {"total": len(all_data), "data": [model.to_dict() for model in all_data]}

# -*- coding: utf-8 -*-
import importlib
import os
import types

from sqlalchemy.dialects.mysql import LONGTEXT

from app.baseModel import BaseModel, db
from utils.globalVariable import FUNC_ADDRESS


class Func(BaseModel):
    """ 自定义函数 """
    __tablename__ = 'func_data'

    name = db.Column(db.String(128), nullable=True, unique=True, comment='脚本名称')
    func_data = db.Column(LONGTEXT, default='', comment='脚本代码')
    desc = db.Column(db.Text(), comment='函数文件描述')

    @classmethod
    def create_func_file(cls, env='test'):
        """ 创建所有自定义函数 py 文件，默认在第一行加上运行环境，默认为test
        示例：
            # coding:utf-8

            env = 'test'

            脚本内容
        """
        for func in cls.get_all():
            func_file_path = os.path.join(FUNC_ADDRESS, f'{env}_{func.name}.py')
            with open(func_file_path, 'w', encoding='utf8') as file:
                file.write('# coding:utf-8\n\n' + f'env = "{env}"\n\n' + func.func_data)

    @classmethod
    def get_func_by_func_file_name(cls, func_file_id_list, env='test'):
        """ 获取指定函数文件中的函数 """
        cls.create_func_file(env)  # 创建所有函数文件
        func_dict = {}
        for func_file_id in func_file_id_list:
            func_list = importlib.reload(
                importlib.import_module(f'func_list.{env}_{Func.get_first(id=func_file_id).name}')
            )
            func_dict.update({
                name: item for name, item in vars(func_list).items() if isinstance(item, types.FunctionType)
            })
        return func_dict

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )

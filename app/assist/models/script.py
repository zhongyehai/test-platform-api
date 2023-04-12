# -*- coding: utf-8 -*-
import importlib
import types

from sqlalchemy.dialects.mysql import LONGTEXT

from app.baseModel import BaseModel, db
from app.config.models.runEnv import RunEnv
from utils.util.fileUtil import FileUtil


class Script(BaseModel):
    """ python脚本 """
    __tablename__ = "python_script"
    __table_args__ = {"comment": "python脚本"}

    name = db.Column(db.String(128), nullable=True, unique=True, comment="脚本名称")
    script_data = db.Column(LONGTEXT, default="", comment="脚本代码")
    desc = db.Column(db.Text(), comment="函数文件描述")
    num = db.Column(db.Integer(), nullable=True, comment="当前函数文件的序号")

    @classmethod
    def create_script_file(cls, env_code=None, not_create_list=[]):
        """ 创建所有自定义函数 py 文件，默认在第一行加上运行环境
        示例：
            # coding:utf-8

            env_code = "test"

            脚本内容
        """
        env = env_code or RunEnv.get_first().code
        for script in cls.get_all():
            if script.name not in not_create_list:
                FileUtil.save_script_data(f"{env}_{script.name}", script.script_data, env)

    @classmethod
    def get_func_by_script_name(cls, func_file_id_list, env_id=None):
        """ 获取指定函数文件中的函数 """
        env = RunEnv.get_first(id=env_id).code if env_id else RunEnv.get_first().code
        cls.create_script_file(env)  # 创建所有函数文件
        func_dict = {}
        for func_file_id in func_file_id_list:
            func_list = importlib.reload(
                importlib.import_module(f"script_list.{env}_{cls.get_first(id=func_file_id).name}")
            )
            func_dict.update({
                name: item for name, item in vars(func_list).items() if isinstance(item, types.FunctionType)
            })
        return func_dict

    @classmethod
    def make_pagination(cls, form, pop_field=['script_data']):
        """ 解析分页条件 """
        filters = []
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        if form.update_user.data:
            filters.append(cls.update_user == form.update_user.data)
        if form.file_name.data:
            filters.append(cls.name.like(f'%{form.file_name.data}%'))

        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc(),
            pop_field=pop_field
        )

# -*- coding: utf-8 -*-
import importlib
import types

from sqlalchemy.dialects.mysql import LONGTEXT

from app.base_model import BaseModel, db
from ...config.model_factory import RunEnv
from utils.util.file_util import FileUtil


class Script(BaseModel):
    """ python脚本 """
    __tablename__ = "python_script"
    __table_args__ = {"comment": "python脚本"}

    name = db.Column(db.String(128), nullable=True, index=True, unique=True, comment="脚本名称")
    script_data = db.Column(LONGTEXT, default="", comment="脚本代码")
    desc = db.Column(db.Text(), comment="函数文件描述")
    num = db.Column(db.Integer(), nullable=True, comment="当前函数文件的序号")
    script_type = db.Column(
        db.String(16), index=True, default="test",
        comment="脚本类型，test：执行测试、mock：mock脚本、encryption：加密、decryption：解密")

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
    def get_func_by_script_id(cls, script_id_list: list, env_id=None):
        """ 获取指定脚本中的函数 """
        env_code = RunEnv.query.first().code if env_id is None else RunEnv.query.filter(id=env_id).first().code
        cls.create_script_file(env_code)  # 创建所有函数文件

        func_dict = {}
        script_name_list = cls.query.with_entities(cls.name).filter(cls.id.in_(script_id_list)).all()
        for script_name in script_name_list:
            func_list = importlib.reload(importlib.import_module(f"script_list.{env_code}_{script_name[0]}"))
            func_dict.update({
                name: item for name, item in vars(func_list).items() if isinstance(item, types.FunctionType)
            })
        return func_dict

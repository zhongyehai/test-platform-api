import re
import importlib
import traceback
from typing import Optional

from pydantic import Field, field_validator
from sqlalchemy.sql import func

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import Script, ScriptMockRecord
from ...config.model_factory import Config
from ...api_test.model_factory import ApiProject, ApiCase
from ...system.model_factory import User
from ...ui_test.model_factory import WebUiProject, WebUiCase
from ...app_test.model_factory import AppUiProject, AppUiCase
from utils.util.file_util import FileUtil


class GetScriptListForm(PaginationForm):
    """ 获取脚本文件列表 """
    file_name: Optional[str] = Field(None, title="脚本名")
    script_type: Optional[str] = Field(None, title="脚本类型")
    create_user: Optional[int] = Field(None, title="创建者")
    update_user: Optional[int] = Field(None, title="修改者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.file_name:
            filter_list.append(Script.name.like(f'%{self.file_name}%'))
        if self.script_type:
            filter_list.append(Script.script_type == self.script_type)
        if self.create_user:
            filter_list.append(Script.create_user == self.create_user)
        return filter_list


class GetScriptForm(BaseForm):
    """ 获取自定义脚本文件 """
    id: int = Field(..., title="脚本文件id")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验自定义脚本文件需存在 """
        script = cls.validate_data_is_exist('数据不存在', Script, id=value)
        setattr(cls, "script", script)
        return value


class DeleteScriptForm(GetScriptForm):
    """ 删除脚本文件 """

    @field_validator("id")
    def validate_id(cls, value):
        """
        1.校验自定义脚本文件需存在
        2.校验是否有引用
        3.校验当前用户是否为管理员或者创建者
        """
        script = cls.validate_data_is_exist('脚本不存在', Script, id=value)

        # 用户是管理员或者创建者
        cls.validate_is_true(
            User.is_admin() or script.current_is_create_user(), "脚本文件仅【管理员】或【当前脚本文件的创建者】可删除")

        # 接口自动化
        query_data = Script.db.session.query(ApiProject.name).filter(func.json_contains(ApiProject.script_list, f'{value}')).first()
        cls.validate_is_false(query_data, f'接口自动化，服务【{query_data}】已引此脚本，请先解除引用')

        # ui自动化
        query_data = Script.db.session.query(WebUiProject.name).filter(func.json_contains(WebUiProject.script_list, f'{value}')).first()
        cls.validate_is_false(query_data, f'ui自动化，服务【{query_data}】已引此脚本，请先解除引用')

        # app自动化
        query_data = Script.db.session.query(AppUiProject.name).filter(func.json_contains(AppUiProject.script_list, f'{value}')).first()
        cls.validate_is_false(query_data, f'app自动化，服务【{query_data}】已引此脚本，请先解除引用')

        setattr(cls, "script", script)
        return value


class DebuggerScriptForm(GetScriptForm):
    """ 调试函数 """
    expression: str = required_str_field(title="调试表达式")
    env: str = required_str_field(title="运行环境")

    @field_validator("expression")
    def validate_expression(cls, value):
        """ 调试表达式 """
        cls.validate_is_true(value.startswith("${") and value.endswith("}"),
                             "调试表达式格式错误，请按照 ${func(abc,123)} 格式填写")
        return value


class CreatScriptForm(BaseForm):
    """ 创建自定义脚本文件 """
    name: str = required_str_field(title="脚本文件名")
    script_type: str = required_str_field(title="脚本类型")
    desc: Optional[str] = Field(None, title="脚本描述")
    script_data: str = required_str_field(title="脚本内容")

    @field_validator("name")
    def validate_name(cls, value):
        cls.validate_is_true(re.match('^[a-zA-Z][a-zA-Z0-9_\\.]+$', value), "脚本文名错误，正确格式为：英文字母开头+英文字母/下划线/数字")
        return value

    def depends_validate(self):
        self.validate_has_permissions()
        self.validate_script_type()
        self.validate_script_data()

    @classmethod
    def validate_has_permissions(cls):
        """ 校验当前用户是否有权限保存脚本文件内容 """
        if Config.get_save_func_permissions() == '1':
            if User.is_not_admin():
                raise ValueError(
                    {"msg": "当前用户暂无权限保存脚本文件内容", "result": "当前用户暂无权限保存脚本文件内容"})

    def validate_script_type(self):
        if self.script_type != 'mock':
            # 防止要改函数时不知道函数属于哪个脚本的情况，强校验函数名必须以脚本名开头
            # importlib.import_module有缓存，所有用正则提取
            functions_name_list = re.findall('\ndef (.+?):', self.script_data)

            for func_name in functions_name_list:
                if func_name.startswith(self.name) is False:
                    raise ValueError(f'函数【{func_name}】命名格式错误，请以【脚本名_函数名】命名')

    def validate_script_data(self):
        """ 校验自定义脚本文件内容合法 """
        default_env = 'debug'

        Script.create_script_file(default_env)  # 把自定义函数脚本内容写入到python脚本中, 重新发版时会把文件全部删除，所以全部创建
        FileUtil.save_script_data(f'{default_env}_{self.name}', self.script_data, env=default_env)

        # 动态导入脚本，语法有错误则不保存
        try:
            script_obj = importlib.reload(importlib.import_module(f'script_list.{default_env}_{self.name}'))
        except Exception as e:
            raise ValueError(
                {"msg": "语法错误，请检查", "result": "\n".join("{}".format(traceback.format_exc()).split("↵"))})


class EditScriptForm(GetScriptForm, CreatScriptForm):
    """ 修改自定义脚本文件 """


class GetRecordListForm(PaginationForm):
    """ 查找服务form """
    name: str = Field(None, title="脚本名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [ScriptMockRecord.name == self.name]
        return filter_list


class GetRecordForm(BaseForm):
    """ 查找服务form """
    id: int = Field(..., title='服务id')

    @field_validator("id")
    def validate_id(cls, value):
        record = cls.validate_data_is_exist("记录不存在", ScriptMockRecord, id=value)
        setattr(cls, "record", record)
        return value

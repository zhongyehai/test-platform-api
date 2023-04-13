# -*- coding: utf-8 -*-
import importlib
import re
import traceback

from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from app.baseForm import BaseForm
from app.api_test.models.project import ApiProject
from app.app_ui_test.models.project import AppUiProject
from app.web_ui_test.models.project import WebUiProject
from app.api_test.models.case import ApiCase
from app.app_ui_test.models.case import AppUiCase
from app.web_ui_test.models.case import WebUiCase
from app.assist.models.script import Script
from app.config.models.config import Config
from utils.util.fileUtil import FileUtil


class GetScriptFileForm(BaseForm):
    """ 获取脚本文件列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    create_user = StringField()
    update_user = StringField()
    file_name = StringField()


class HasScriptForm(BaseForm):
    """ 获取自定义脚本文件 """
    id = IntegerField(validators=[DataRequired("请输选择脚本文件")])

    def validate_id(self, field):
        """ 校验自定义脚本文件需存在 """
        script = self.validate_data_is_exist(f'id为 【{field.data}】 的脚本文件不存在', Script, id=field.data)
        setattr(self, "script", script)


class CreatScriptForm(BaseForm):
    """ 创建自定义脚本文件 """
    name = StringField(validators=[DataRequired("请输入脚本文件名")])
    desc = StringField()
    num = StringField()
    script_data = StringField()

    def validate_name(self, field):
        """ 校验Python脚本文件名 """
        self.validate_data_is_true(f"脚本文名错误，支持大小写字母和下划线", re.match('^[a-zA-Z_]+$', field.data))
        self.validate_data_is_not_exist(f"脚本文件【{field.data}】已经存在", Script, name=field.data)

    def validate_script_data(self, field):
        """ 校验自定义脚本文件内容合法 """
        default_env = 'debug'
        if field.data:
            # 校验当前用户是否有权限保存脚本文件内容
            if Config.get_save_func_permissions() == '1':
                if self.is_not_admin():
                    raise ValidationError({
                        "msg": "当前用户暂无权限保存脚本文件内容",
                        "result": "当前用户暂无权限保存脚本文件内容"
                    })

            # 防止要改函数时不知道函数属于哪个脚本的情况，强校验函数名必须以脚本名开头
            # importlib.import_module有缓存，所有用正则提取
            functions_name_list = re.findall('\ndef (.+?):', self.script_data.data)

            for func_name in functions_name_list:
                if func_name.startswith(self.name.data) is False:
                    raise ValidationError(f'函数【{func_name}】命名格式错误，请以【脚本名_函数名】命名')

            # 把自定义函数脚本内容写入到python脚本中,
            Script.create_script_file(default_env)  # 重新发版时会把文件全部删除，所以全部创建
            FileUtil.save_script_data(f'{default_env}_{self.name.data}', self.script_data.data, env=default_env)

            # 动态导入脚本，语法有错误则不保存
            try:
                script_obj = importlib.reload(importlib.import_module(f'script_list.{default_env}_{self.name.data}'))
            except Exception as e:
                raise ValidationError({
                    "msg": "语法错误，请检查",
                    "result": "\n".join("{}".format(traceback.format_exc()).split("↵"))
                })


class EditScriptForm(HasScriptForm, CreatScriptForm):
    """ 修改自定义脚本文件 """

    def validate_name(self, field):
        """ 校验Python脚本文件 """
        self.validate_data_is_not_repeat(
            f"脚本文件【{field.data}】已经存在",
            Script,
            self.id.data,
            name=field.data
        )


class DebuggerScriptForm(HasScriptForm):
    """ 调试函数 """
    expression = StringField(validators=[DataRequired("请输入调试表达式")])
    env = StringField(validators=[DataRequired("请选择环境")])

    # def validate_debug_data(self, field):
    #     if not re.findall(r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}", field.data):
    #         raise ValidationError("格式错误，请使用【 ${func(*args)} 】格式")


class DeleteScriptForm(BaseForm):
    """ 删除脚本文件 """

    id = StringField(validators=[DataRequired("脚本文件id必传")])

    def validate_id(self, field):
        """
        1.校验自定义脚本文件需存在
        2.校验是否有引用
        3.校验当前用户是否为管理员或者创建者
        """
        script = self.validate_data_is_exist(f"脚本文件【{field.data}】不存在", Script, id=field.data)

        # 校验是否被引用
        for model in [ApiProject, AppUiProject, WebUiProject, ApiCase, AppUiCase, WebUiCase]:
            data_like = model.query.filter(model.script_list.like(f"%{field.data}%")).all()
            if data_like:
                for data in data_like:
                    if field.data in data.to_dict().get("script_list", []):
                        class_name = type(data).__name__

                        if 'Project' in class_name:
                            name = '服务' if 'Api' in class_name else '项目' if 'WebUi' in class_name else 'APP'
                            raise ValidationError(
                                f"{name}【{model.get_first(id=data.id).name}】已引用此脚本文件，请先解除依赖再删除"
                            )
                        else:
                            name = '接口' if 'Api' in class_name else 'WebUi' if 'WebUi' in class_name else 'APP'
                        raise ValidationError(
                            f"{name}测试用例【{model.get_first(id=data.id).name}】已引用此脚本文件，请先解除依赖再删除"
                        )

        # 用户是管理员或者创建者
        self.validate_data_is_true(
            "脚本文件仅【管理员】或【当前脚本文件的创建者】可删除",
            self.is_admin() or script.is_create_user(g.user_id)
        )
        setattr(self, "script", script)

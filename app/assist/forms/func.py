# -*- coding: utf-8 -*-
import importlib
import traceback

from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from app.baseForm import BaseForm
from app.api_test.models.case import ApiCase
from app.api_test.models.project import ApiProject
from app.assist.models.func import Func
from app.config.models.config import Config
from app.system.models.user import User
from utils.util.fileUtil import FileUtil


class GetFuncFileForm(BaseForm):
    """ 获取函数文件列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    create_user = StringField()
    update_user = StringField()
    file_name = StringField()


class HasFuncForm(BaseForm):
    """ 获取自定义函数文件 """
    id = IntegerField(validators=[DataRequired("请输选择函数文件")])

    def validate_id(self, field):
        """ 校验自定义函数文件需存在 """
        func = self.validate_data_is_exist(f'id为 【{field.data}】 的函数文件不存在', Func, id=field.data)
        setattr(self, "func", func)


class SaveFuncDataForm(HasFuncForm):
    """ 修改自定义函数文件内容 """
    func_data = StringField()

    def validate_func_data(self, field):
        """ 校验自定义函数文件内容合法 """

        # 校验当前用户是否有权限保存函数文件内容
        if Config.get_save_func_permissions() == '1':
            if not g.user_role or User.is_admin(g.user_id) is False:
                raise ValidationError({
                    "msg": "当前用户暂无权限保存函数文件内容",
                    "result": "当前用户暂无权限保存函数文件内容"
                })

        # 把自定义函数脚本内容写入到python脚本中
        FileUtil.save_func_data(self.func.name, field.data)

        # 动态导入脚本，语法有错误则不保存
        try:
            importlib.reload(importlib.import_module(f'func_list.{self.func.name}'))
        except Exception as e:
            raise ValidationError({
                "msg": "语法错误，请检查",
                "result": "\n".join("{}".format(traceback.format_exc()).split("↵"))
            })


class CreatFuncForm(BaseForm):
    """ 创建自定义函数文件 """
    name = StringField(validators=[DataRequired("请输入函数文件名")])
    desc = StringField()
    num = StringField()

    def validate_name(self, field):
        """ 校验Python函数文件 """
        self.validate_data_is_not_exist(f"函数文件【{field.data}】已经存在", Func, name=field.data)


class EditFuncForm(HasFuncForm, CreatFuncForm):
    """ 修改自定义函数文件 """

    def validate_name(self, field):
        """ 校验Python函数文件 """
        self.validate_data_is_not_repeat(
            f"函数文件【{field.data}】已经存在",
            Func,
            self.id.data,
            name=field.data
        )


class DebuggerFuncForm(HasFuncForm):
    """ 调试函数 """
    debug_data = StringField(validators=[DataRequired("请输入要调试的函数")])

    # def validate_debug_data(self, field):
    #     if not re.findall(r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}", field.data):
    #         raise ValidationError("格式错误，请使用【 ${func(*args)} 】格式")


class DeleteFuncForm(BaseForm):
    """ 删除f函数文件 """

    id = StringField(validators=[DataRequired("函数文件id必传")])

    def validate_id(self, field):
        """
        1.校验自定义函数文件需存在
        2.校验是否有引用
        3.校验当前用户是否为管理员或者创建者
        """
        func = self.validate_data_is_exist(f"函数文件【{field.data}】不存在", Func, id=field.data)

        # 服务引用
        project_like = ApiProject.query.filter(ApiProject.func_files.like(f"%{field.data}%")).all()
        if project_like:
            for project in project_like:
                if field.data in project.to_dict().get("func_files", []):
                    raise ValidationError(
                        f"服务【{ApiProject.get_first(id=project.id).name}】已引用此函数文件，请先解除依赖再删除")

        # project = ApiProject.query.filter(ApiProject.func_files.like(f"%{field.data}%")).first()
        # if project:
        #     raise ValidationError(f"服务【{ApiProject.get_first(id=project).name}】已引用此函数文件，请先解除依赖再删除")

        # 用例引用
        case = ApiCase.query.filter(ApiCase.func_files.like(f"%{field.data}%")).first()
        if case:
            raise ValidationError(f"用例【{case.name}】已引用此函数文件，请先解除依赖再删除")

        # 用户是管理员或者创建者
        self.validate_data_is_true(
            "函数文件仅【管理员】或【当前函数文件的创建者】可删除",
            self.is_admin() or func.is_create_user(g.user_id)
        )
        setattr(self, "func", func)

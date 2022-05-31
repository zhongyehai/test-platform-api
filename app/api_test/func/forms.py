# -*- coding: utf-8 -*-
import os
import importlib
import traceback

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from flask_login import current_user

from app.baseForm import BaseForm
from app.api_test.case.models import ApiCase
from app.api_test.project.models import ApiProject
from .models import Func
from ...utils.globalVariable import FUNC_ADDRESS


class GetFuncFileForm(BaseForm):
    """ 获取函数文件列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()


class HasFuncForm(BaseForm):
    """ 获取自定义函数文件 """
    id = IntegerField(validators=[DataRequired('请输选择函数文件')])

    def validate_id(self, field):
        """ 校验自定义函数文件需存在 """
        func = Func.get_first(id=field.data)
        if not func:
            raise ValidationError(f'id为 【{field.data}】 的函数文件不存在')
        setattr(self, 'func', func)


class SaveFuncDataForm(HasFuncForm):
    """ 修改自定义函数文件 """
    func_data = StringField()

    def validate_func_data(self, field):
        """ 校验自定义函数文件内容合法 """

        # 把自定义函数脚本内容写入到python脚本中
        with open(os.path.join(FUNC_ADDRESS, f'{self.func.name}.py'), 'w', encoding='utf8') as file:
            # file.write(field.data)
            file.write('# coding:utf-8\n\n' + f'env = "test"\n\n' + field.data)

        # 动态导入脚本，语法有错误则不保存
        try:
            importlib.reload(importlib.import_module(f'func_list.{self.func.name}'))
        except Exception as e:
            raise ValidationError({
                'msg': '语法错误，请检查',
                'result': '\n'.join('{}'.format(traceback.format_exc()).split('↵'))
            })


class CreatFuncForm(BaseForm):
    """ 创建自定义函数文件 """
    name = StringField(validators=[DataRequired('请输入函数文件名')])
    desc = StringField()

    def validate_name(self, field):
        """ 校验Python函数文件 """
        if Func.get_first(name=field.data):
            raise ValidationError(f'函数文件【{field.data}】已经存在')


class EditFuncForm(HasFuncForm):
    """ 修改自定义函数文件 """
    name = StringField(validators=[DataRequired('请输入函数文件名')])
    desc = StringField()

    def validate_name(self, field):
        """ 校验Python函数文件 """
        old = Func.get_first(name=field.data)
        if old and old.id != self.id.data:
            raise ValidationError(f'函数文件【{field.data}】已经存在')


class DebuggerFuncForm(HasFuncForm):
    """ 调试函数 """
    debug_data = StringField(validators=[DataRequired('请输入要调试的函数')])

    # def validate_debug_data(self, field):
    #     if not re.findall(r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}", field.data):
    #         raise ValidationError('格式错误，请使用【 ${func(*args)} 】格式')


class DeleteFuncForm(BaseForm):
    """ 删除form """

    name = StringField(validators=[DataRequired('函数文件必传')])

    def validate_name(self, field):
        """
        1.校验自定义函数文件需存在
        2.校验是否有引用
        3.校验当前用户是否为管理员或者创建者
        """
        func = Func.get_first(name=field.data)
        if not func:
            raise ValidationError(f'函数文件【{field.data}】不存在')
        else:
            # 服务引用
            project = ApiProject.query.filter(ApiProject.func_files.like(f'%{field.data}%')).first()
            if project:
                raise ValidationError(f'服务【{project.name}】已引用此函数文件，请先解除依赖再删除')
            # 用例引用
            case = ApiCase.query.filter(ApiCase.func_files.like(f'%{field.data}%')).first()
            if case:
                raise ValidationError(f'用例【{case.name}】已引用此函数文件，请先解除依赖再删除')
            # 用户是管理员或者创建者
            if self.is_not_admin() and not func.is_create_user(current_user.id):
                raise ValidationError('函数文件仅【管理员】或【当前函数文件的创建者】可删除')
        setattr(self, 'func', func)

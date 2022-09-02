# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from app.api_test.models.case import ApiCase as Case
from app.assist.models.func import Func
from app.api_test.models.step import ApiStep as Step
from app.api_test.models.api import ApiMsg
from app.api_test.models.module import ApiModule
from app.api_test.models.project import ApiProject, ApiProjectEnv


class GetApiByIdForm(BaseForm):
    """ 获取api信息 """
    id = IntegerField(validators=[DataRequired('接口id必传')])

    def validate_id(self, field):
        api = self.validate_data_is_exist(f'id为【{field.data}】的接口不存在', ApiMsg, id=field.data)
        setattr(self, 'api', api)


class AddApiForm(BaseForm):
    """ 添加接口信息的校验 """
    project_id = StringField(validators=[DataRequired('服务id必传')])
    module_id = StringField(validators=[DataRequired('模块id必传')])

    name = StringField(validators=[DataRequired('接口名必传'), Length(1, 255, '接口名长度为1~255位')])
    desc = StringField()
    up_func = StringField()  # 前置条件
    down_func = StringField()  # 后置条件
    method = StringField(validators=[DataRequired('请求方法必传'), Length(1, 10, message='请求方法长度为1~10位')])
    addr = StringField(validators=[DataRequired('接口地址必传')])
    headers = StringField()
    params = StringField()
    data_type = StringField()
    data_form = StringField()
    data_json = StringField()
    data_urlencoded = StringField()
    data_text = StringField()
    extracts = StringField()
    validates = StringField()
    num = StringField()
    time_out = IntegerField()
    project = None

    def validate_project_id(self, field):
        """ 校验服务id """
        self.project = self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)
        setattr(self, 'project', self.project)

    def validate_module_id(self, field):
        """ 校验模块id """
        self.validate_data_is_exist(f'id为【{field.data}】的模块不存在', ApiModule, id=field.data)

    def validate_name(self, field):
        """ 校验同一模块下接口名不重复 """
        self.validate_data_is_not_exist(
            f'当前模块下，名为【{field.data}】的接口已存在',
            ApiMsg,
            name=field.data,
            module_id=self.module_id.data
        )

    def validate_addr(self, field):
        """ 接口地址校验 """
        self.validate_data_is_true('接口地址不能为空', field.data.split('?')[0])

    def validate_extracts(self, field):
        """ 校验提取数据表达式 """
        self.validate_base_extracts(field.data)

    def validate_validates(self, field):
        """ 校验断言表达式 """
        func_container = Func.get_func_by_func_file_name(self.loads(self.project.func_files))
        self.validate_base_validates(field.data, func_container)


class EditApiForm(GetApiByIdForm, AddApiForm):
    """ 修改接口信息 """

    def validate_name(self, field):
        """ 校验接口名不重复 """
        self.validate_data_is_not_repeat(
            f'当前模块下，名为【{field.data}】的接口已存在',
            ApiMsg,
            self.id.data,
            name=field.data,
            module_id=self.module_id.data
        )


class RunApiMsgForm(BaseForm):
    """ 运行接口 """
    projectId = IntegerField(validators=[DataRequired('服务id必传')])
    apis = StringField(validators=[DataRequired('请选择接口，再进行测试')])
    env = StringField(validators=[DataRequired('请选择运行环境')])

    def validate_projectId(self, field):
        """ 校验服务id """
        self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)

    def validate_apis(self, field):
        """ 校验接口存在 """
        self.validate_data_is_true('接口id必传', self.apis.data)
        api_list = []
        for api_id in self.apis.data:
            api_list.append(self.validate_data_is_exist(f'id为【{api_id}】的接口不存在', ApiMsg, id=api_id))
        setattr(self, 'api_list', api_list)


class ApiListForm(BaseForm):
    """ 查询接口信息 """
    moduleId = IntegerField(validators=[DataRequired('请选择模块')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class ApiBelongToForm(BaseForm):
    """ 查询api归属 """
    addr = StringField(validators=[DataRequired('接口地址必传')])

    def validate_addr(self, field):
        api = self.validate_data_is_exist(f'地址为【{field.data}】的接口不存在', ApiMsg, addr=field.data)
        setattr(self, 'api', api)


class DeleteApiForm(GetApiByIdForm):
    """ 删除接口 """

    def validate_id(self, field):
        api = self.validate_data_is_exist(f'id为【{field.data}】的接口不存在', ApiMsg, id=field.data)

        # 校验接口是否被测试用例引用
        case_data = Step.get_first(api_id=field.data)
        if case_data:
            case = Case.get_first(id=case_data.case_id)
            raise ValidationError(f'用例【{case.name}】已引用此接口，请先解除引用')

        self.validate_data_is_true(
            '不能删除别人服务下的接口',
            ApiProject.is_can_delete(ApiModule.get_first(id=api.module_id).project_id, api)
        )
        setattr(self, 'api', api)

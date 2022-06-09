# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from ..case.models import ApiCase as Case
from ..func.models import Func
from ..step.models import ApiStep as Step
from ..apiMsg.models import ApiMsg
from ..module.models import ApiModule
from ..project.models import ApiProject, ApiProjectEnv


class AddApiForm(BaseForm):
    """ 添加接口信息的校验 """
    project_id = StringField(validators=[DataRequired('服务id必传')])
    module_id = StringField(validators=[DataRequired('模块id必传')])

    name = StringField(validators=[DataRequired('接口名必传'), Length(1, 255, '接口名长度为1~255位')])
    desc = StringField()
    up_func = StringField()  # 前置条件
    down_func = StringField()  # 后置条件
    method = StringField(validators=[DataRequired('请求方法必传'), Length(1, 10, message='请求方法长度为1~10位')])
    choice_host = StringField(validators=[DataRequired('请选择要运行的环境')])
    addr = StringField(validators=[DataRequired('接口地址必传')])
    headers = StringField()
    params = StringField()
    data_type = StringField()
    data_form = StringField()
    data_json = StringField()
    data_xml = StringField()
    extracts = StringField()
    validates = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 校验服务id """
        project = ApiProject.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的服务不存在')
        setattr(self, 'project', project)

    def validate_module_id(self, field):
        """ 校验模块id """
        if not ApiModule.get_first(id=field.data):
            raise ValidationError(f'id为【{field.data}】的模块不存在')

    def validate_name(self, field):
        """ 校验同一模块下接口名不重复 """
        if ApiMsg.get_first(name=field.data, module_id=self.module_id.data):
            raise ValidationError(f'当前模块下，名为【{field.data}】的接口已存在')

    def validate_addr(self, field):
        """ 接口地址校验 """
        if not field.data.split('?')[0]:
            raise ValidationError('接口地址不能为空')

    def validate_choice_host(self, field):
        """ 保存接口时，判断项目对应接口选择的环境是否已设置 """
        env = ApiProjectEnv.get_first(project_id=self.project_id.data, env=field.data)
        if not env.host:
            raise ValidationError('此接口所在的服务未设置当前选择环境的域名')

    def validate_extracts(self, field):
        """ 校验提取数据表达式 """
        self.validate_base_extracts(field.data)

    def validate_validates(self, field):
        """ 校验断言表达式 """
        func_files = self.loads(
            ApiProjectEnv.get_first(project_id=self.project.id, env=self.choice_host.data).func_files)
        func_container = Func.get_func_by_func_file_name(func_files)
        self.validate_base_validates(field.data, func_container)


class EditApiForm(AddApiForm):
    """ 修改接口信息 """
    id = IntegerField(validators=[DataRequired('接口id必传')])

    def validate_id(self, field):
        """ 校验接口id已存在 """
        old = ApiMsg.get_first(id=field.data)
        if not old:
            raise ValidationError(f'id为【{field.data}】的接口不存在')
        setattr(self, 'old', old)

    def validate_name(self, field):
        """ 校验接口名不重复 """
        old_api = ApiMsg.get_first(name=field.data, module_id=self.module_id.data)
        if old_api and old_api.id != self.id.data:
            raise ValidationError(f'当前模块下，名为【{field.data}】的接口已存在')


class ValidateProjectId(BaseForm):
    """ 校验服务id """
    projectId = IntegerField(validators=[DataRequired('服务id必传')])

    def validate_projectId(self, field):
        """ 校验服务id """
        if not ApiProject.get_first(id=field.data):
            raise ValidationError(f'id为【{field.data}】的服务不存在')


class RunApiMsgForm(ValidateProjectId):
    """ 运行接口 """
    apis = StringField(validators=[DataRequired('请选择接口，再进行测试')])

    def validate_apis(self, field):
        """ 校验接口存在 """
        api = ApiMsg.get_first(id=field.data)
        if not api:
            raise ValidationError(f'id为【{field.data}】的接口不存在')
        setattr(self, 'api', api)


class ApiListForm(BaseForm):
    """ 查询接口信息 """
    moduleId = IntegerField(validators=[DataRequired('请选择模块')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetApiById(BaseForm):
    """ 待编辑信息 """
    id = IntegerField(validators=[DataRequired('接口id必传')])

    def validate_id(self, field):
        api = ApiMsg.get_first(id=field.data)
        if not api:
            raise ValidationError(f'id为【{field.data}】的接口不存在')
        setattr(self, 'api', api)


class ApiBelongToForm(BaseForm):
    """ 查询api归属 """
    addr = StringField(validators=[DataRequired('接口地址必传')])

    def validate_addr(self, field):
        api = ApiMsg.get_first(addr=field.data)
        if not api:
            raise ValidationError(f'地址为【{field.data}】的接口不存在')
        setattr(self, 'api', api)


class DeleteApiForm(GetApiById):
    """ 删除接口 """

    def validate_id(self, field):
        api = ApiMsg.get_first(id=field.data)
        if not api:
            raise ValidationError(f'id为【{field.data}】的接口不存在')

        # 校验接口是否被测试用例引用
        case_data = Step.get_first(api_id=field.data)
        if case_data:
            case = Case.get_first(id=case_data.case_id)
            raise ValidationError(f'用例【{case.name}】已引用此接口，请先解除引用')

        project_id = ApiModule.get_first(id=api.module_id).project_id
        if not ApiProject.is_can_delete(project_id, api):
            raise ValidationError('不能删除别人服务下的接口')
        setattr(self, 'api', api)

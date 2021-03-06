# -*- coding: utf-8 -*-

import validators
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.ui_test.models.project import UiProject, UiProjectEnv
from app.ucenter.models.user import User
from app.ui_test.models.module import UiModule


class AddUiProjectForm(BaseForm):
    """ 添加项目参数校验 """
    name = StringField(validators=[DataRequired('项目名称不能为空'), Length(1, 255, message='项目名长度不可超过255位')])
    manager = StringField(validators=[DataRequired('请选择负责人')])
    swagger = StringField()

    def validate_name(self, field):
        """ 校验项目名不重复 """
        self.validate_data_is_not_exist(f'项目名【{field.data}】已存在', UiProject, name=field.data)

    def validate_manager(self, field):
        """ 校验项目负责人是否存在 """
        self.validate_data_is_exist(f'id为【{field.data}】的用户不存在', User, id=field.data)

    def validate_swagger(self, field):
        """ 校验swagger地址是否正确 """
        self.validate_data_is_false(
            f'swagger地址【{field.data}】不正确',
            field.data and validators.url(field.data) is not True
        )


class FindUiProjectForm(BaseForm):
    """ 查找项目form """
    name = StringField()
    manager = StringField()
    create_user = StringField()
    projectId = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetUiProjectByIdForm(BaseForm):
    """ 获取具体项目信息 """
    id = IntegerField(validators=[DataRequired('项目id必传')])

    def validate_id(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在', UiProject, id=field.data)
        setattr(self, 'project', project)


class DeleteUiProjectForm(GetUiProjectByIdForm):
    """ 删除项目 """

    def validate_id(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在', UiProject, id=field.data)
        self.validate_data_is_true('不能删除别人负责的项目', self.is_can_delete(project.id, project))
        self.validate_data_is_not_exist('请先去【页面管理】删除项目下的模块', UiModule, project_id=field.data)
        setattr(self, 'project', project)


class EditUiProjectForm(GetUiProjectByIdForm, AddUiProjectForm):
    """ 修改项目参数校验 """

    def validate_name(self, field):
        """ 校验项目名不重复 """
        self.validate_data_is_not_repeat(
            f'项目名【{field.data}】已存在',
            UiProject,
            self.id.data,
            name=field.data
        )


class AddEnv(BaseForm):
    """ 添加环境 """
    project_id = IntegerField(validators=[DataRequired('项目id必传')])
    env = StringField(validators=[DataRequired('所属环境必传'), Length(1, 10, message='所属环境长度为1~10位')])
    host = StringField(validators=[DataRequired('域名必传'), Length(2, 255, message='域名长度为1~255位')])
    variables = StringField()
    cookies = StringField()
    session_storage = StringField()
    local_storage = StringField()
    func_files = StringField()
    all_func_name = {}
    all_variables = {}

    def validate_project_id(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在', UiProject, id=field.data)
        setattr(self, 'project', project)

    def validate_host(self, field):
        """ 校验地址是否正确 """
        self.validate_data_is_true(f'环境地址【{field.data}】不正确', field.data and validators.url(field.data) is True)

    # def validate_headers(self, field):
    #     """ 校验头部信息是否有引用自定义函数 """
    #     self.validate_variable_and_header_format(field.data, '头部信息设置，第【', '】行，要设置头部信息，则key和value都需设置')
    #     self.validate_func(self.all_func_name, self.func_files.data, self.dumps(field.data))  # 自定义函数
    #     self.validate_variable(self.all_variables, self.variables.data, self.dumps(field.data))  # 公共变量

    def validate_variables(self, field):
        """ 校验公共变量 """
        self.validate_variable_and_header_format(field.data, '自定义变量设置，，第【', '】行，要设置自定义变量，则key和value都需设置')
        self.validate_func(self.all_func_name, self.func_files.data, self.dumps(field.data))  # 自定义函数
        self.validate_variable(self.all_variables, field.data, self.dumps(field.data))  # 公共变量


class EditEnv(AddEnv):
    """ 修改环境 """
    id = IntegerField(validators=[DataRequired('环境id必传')])

    def validate_env(self, field):
        env_data = self.validate_data_is_exist(
            '当前环境不存在',
            UiProjectEnv,
            project_id=self.project_id.data,
            env=field.data
        )
        setattr(self, 'env_data', env_data)


class FindEnvForm(BaseForm):
    """ 查找项目环境form """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    env = StringField()

    def validate_projectId(self, field):
        env_data = UiProjectEnv.get_first(project_id=field.data, env=self.env.data)
        if not env_data:  # 如果没有就插入一条记录
            env_data = UiProjectEnv().create({"env": self.env.data, "project_id": field.data})
            setattr(self, 'env_data', env_data)
        setattr(self, 'env_data', env_data)


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    envFrom = StringField(validators=[DataRequired('所属环境必传'), Length(1, 10, message='所属环境长度为1~10位')])
    envTo = StringField(validators=[DataRequired('所属环境必传'), Length(1, 10, message='所属环境长度为1~10位')])

    def validate_projectId(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在', UiProject, id=field.data)
        setattr(self, 'project', project)

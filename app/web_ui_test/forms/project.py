# -*- coding: utf-8 -*-
import validators
from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired, ValidationError

from app.assist.models.script import Script
from app.baseForm import BaseForm
from app.web_ui_test.models.project import WebUiProject as Project, WebUiProjectEnv as ProjectEnv
from app.system.models.user import User
from app.web_ui_test.models.module import WebUiModule as Module


class AddUiProjectForm(BaseForm):
    """ 添加项目参数校验 """
    name = StringField(validators=[DataRequired("项目名称不能为空"), Length(1, 255, message="项目名长度不可超过255位")])
    manager = StringField(validators=[DataRequired("请选择负责人")])
    business_id = StringField(validators=[DataRequired("请选择业务线")])
    script_list = StringField()
    num = StringField()

    def validate_name(self, field):
        """ 校验项目名不重复 """
        self.validate_data_is_not_exist(f"项目名【{field.data}】已存在", Project, name=field.data)

    def validate_manager(self, field):
        """ 校验项目负责人是否存在 """
        self.validate_data_is_exist(f"id为【{field.data}】的用户不存在", User, id=field.data)


class FindUiProjectForm(BaseForm):
    """ 查找项目form """
    name = StringField()
    manager = StringField()
    business_id = IntegerField()
    create_user = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()

    def validate_business_id(self, filed):
        if self.is_not_admin():
            if filed.data and (filed.data not in g.business_list):
                raise ValidationError("当前用户没有权限")


class GetUiProjectByIdForm(BaseForm):
    """ 获取具体项目信息 """
    id = IntegerField(validators=[DataRequired("项目id必传")])

    def validate_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)
        setattr(self, "project", project)


class DeleteUiProjectForm(GetUiProjectByIdForm):
    """ 删除项目 """

    def validate_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)
        self.validate_data_is_true("不能删除别人负责的项目", self.is_can_delete(project.id, project))
        self.validate_data_is_not_exist("请先去【页面管理】删除项目下的模块", Module, project_id=field.data)
        setattr(self, "project", project)


class EditUiProjectForm(GetUiProjectByIdForm, AddUiProjectForm):
    """ 修改项目参数校验 """

    def validate_name(self, field):
        """ 校验项目名不重复 """
        self.validate_data_is_not_repeat(
            f"项目名【{field.data}】已存在",
            Project,
            self.id.data,
            name=field.data
        )


class AddEnv(BaseForm):
    """ 添加环境 """
    project_id = IntegerField(validators=[DataRequired("项目id必传")])
    env_id = IntegerField(validators=[DataRequired("所属环境必传")])
    host = StringField(validators=[DataRequired("域名必传")])
    variables = StringField()
    all_func_name = {}
    all_variables = {}

    def validate_host(self, field):
        if validators.url(field.data) is not True:
            raise ValidationError(f"环境地址【{field.data}】不正确，请输入正确的格式")

    def validate_project_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)
        self.all_func_name = Script.get_func_by_script_name(self.loads(project.script_list), self.env_id.data)
        setattr(self, "project", project)

    def validate_variables(self, field):
        """ 校验公共变量 """
        self.validate_variable_format(field.data)
        self.validate_func(self.all_func_name, self.dumps(field.data))  # 自定义函数
        self.validate_variable(self.all_variables, field.data, self.dumps(field.data))  # 公共变量


class EditEnv(AddEnv):
    """ 修改环境 """
    id = IntegerField(validators=[DataRequired("环境id必传")])

    def validate_id(self, field):
        env_data = self.validate_data_is_exist(
            "当前环境不存在",
            ProjectEnv,
            id=field.data
        )
        setattr(self, "env_data", env_data)


class FindEnvForm(BaseForm):
    """ 查找项目环境form """
    projectId = IntegerField(validators=[DataRequired("项目id必传")])
    env_id = StringField()

    def validate_projectId(self, field):
        env_data = ProjectEnv.get_first(project_id=field.data, env_id=self.env_id.data)
        if not env_data:  # 如果没有就插入一条记录， 并且自动同步当前服务已有的环境数据
            project_other_env = ProjectEnv.get_first(project_id=field.data)
            if project_other_env:
                insert_env_data = project_other_env.to_dict()
                insert_env_data["env_id"] = self.env_id.data
            else:
                insert_env_data = {"env_id": self.env_id.data, "project_id": field.data}
            env_data = ProjectEnv().create(insert_env_data)
        setattr(self, "env_data", env_data)


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    projectId = IntegerField(validators=[DataRequired("项目id必传")])
    envFrom = StringField()
    envTo = StringField()

    def validate_projectId(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)
        setattr(self, "project", project)

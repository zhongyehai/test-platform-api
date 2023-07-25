# -*- coding: utf-8 -*-
import validators
from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired, ValidationError

from app.assist.models.script import Script
from app.baseForm import BaseForm
from app.app_ui_test.models.project import AppUiProject as Project, AppUiProjectEnv as ProjectEnv
from app.system.models.user import User
from app.app_ui_test.models.module import AppUiModule as Module


class AddUiProjectForm(BaseForm):
    """ 添加app参数校验 """
    name = StringField(validators=[DataRequired("app名称不能为空"), Length(1, 255, message="app名长度不可超过255位")])
    manager = StringField(validators=[DataRequired("请选择负责人")])
    app_package = StringField(validators=[DataRequired("app包名不能为空")])
    app_activity = StringField(validators=[DataRequired("activity不能为空")])
    business_id = StringField(validators=[DataRequired("请选择业务线")])
    template_device = IntegerField(validators=[DataRequired("请选择元素定位时参照的设备")])
    script_list = StringField()
    num = StringField()

    def validate_name(self, field):
        """ 校验app名不重复 """
        self.validate_data_is_not_exist(f"app名【{field.data}】已存在", Project, name=field.data)

    def validate_manager(self, field):
        """ 校验app负责人是否存在 """
        self.validate_data_is_exist(f"id为【{field.data}】的用户不存在", User, id=field.data)

    def validate_swagger(self, field):
        """ 校验swagger地址是否正确 """
        self.validate_data_is_false(
            f"swagger地址【{field.data}】不正确",
            field.data and validators.url(field.data) is not True
        )


class FindUiProjectForm(BaseForm):
    """ 查找appform """
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
    """ 获取具体app信息 """
    id = IntegerField(validators=[DataRequired("appid必传")])

    def validate_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的app不存在", Project, id=field.data)
        setattr(self, "project", project)


class DeleteUiProjectForm(GetUiProjectByIdForm):
    """ 删除app """

    def validate_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的app不存在", Project, id=field.data)
        self.validate_data_is_true("不能删除别人负责的app", self.is_can_delete(project.id, project))
        self.validate_data_is_not_exist("请先去【页面管理】删除app下的模块", Module, project_id=field.data)
        setattr(self, "project", project)


class EditUiProjectForm(GetUiProjectByIdForm, AddUiProjectForm):
    """ 修改app参数校验 """

    def validate_name(self, field):
        """ 校验app名不重复 """
        self.validate_data_is_not_repeat(
            f"app名【{field.data}】已存在",
            Project,
            self.id.data,
            name=field.data
        )


class AddEnv(BaseForm):
    """ 添加环境 """
    project_id = IntegerField(validators=[DataRequired("appid必传")])
    variables = StringField()
    all_func_name = {}
    all_variables = {}

    def validate_project_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的app不存在", Project, id=field.data)
        self.all_func_name = Script.get_func_by_script_name(self.loads(project.script_list))
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
    """ 查找app环境form """
    projectId = IntegerField(validators=[DataRequired("appid必传")])
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

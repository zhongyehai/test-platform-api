# -*- coding: utf-8 -*-
from typing import Optional, Union, List

from flask import g
from sqlalchemy import or_
from pydantic import field_validator, ValidationInfo

from ...base_form import BaseForm, Field, PaginationForm, ValidateModel, required_str_field
from ..model_factory import AppUiProject as Project, AppUiProjectEnv as ProjectEnv, AppUiModule as Module, \
    AppUiCaseSuite as CaseSuite, AppUiTask as Task
from ...system.models.user import User
from ...assist.models.script import Script


class GetProjectListForm(PaginationForm):
    """ 查找APPform """
    name: Optional[str] = Field(None, title="APP名")
    manager: Optional[Union[int, str]] = Field(None, title="负责人")
    business_id: Optional[int] = Field(None, title="所属业务线")
    create_user: Optional[Union[int, str]] = Field(None, title="创建者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.business_id:  # 传了业务线id，就获取对应的业务线的APP
            filter_list.append(Project.business_id == self.business_id)
        else:
            if User.is_not_admin():  # 非管理员
                filter_list.append(Project.business_id.in_(g.business_list))
        if self.name:
            filter_list.append(Project.name.like(f'%{self.name}%'))
        if self.manager:
            filter_list.append(Project.manager == self.manager)
        if self.business_id:
            filter_list.append(Project.business_id == self.business_id)
        if self.create_user:
            filter_list.append(Project.create_user == self.create_user)
        return filter_list


class GetProjectForm(BaseForm):
    """ 获取具体app信息 """
    id: int = Field(..., title='APP id')

    @field_validator("id")
    def validate_id(cls, value):
        project = cls.validate_data_is_exist("APP不存在", Project, id=value)
        setattr(cls, "project", project)
        return value


class DeleteProjectForm(GetProjectForm):
    """ 删除app """

    @field_validator("id")
    def validate_id(cls, value):
        cls.validate_is_true(Project.is_can_delete(value), "不能删除别人负责的APP")
        cls.validate_is_false(
            Module.db.session.query(Module.id).filter(Module.project_id == value).first(), '服务下有模块,不允许删除')
        cls.validate_is_false(
            CaseSuite.db.session.query(CaseSuite.id).filter(CaseSuite.project_id == value).first(),
            '服务下有用例集,不允许删除')
        cls.validate_is_false(
            Task.db.session.query(Task.id).filter(Task.project_id == value).first(), '服务下有任务，不允许删除')
        return value


class AddProjectForm(BaseForm):
    """ 添加app参数校验 """
    name: str = required_str_field(title="app名称")
    manager: int = Field(..., title="负责人")
    business_id: int = Field(..., title="业务线")
    app_package: str = required_str_field(title="app包名")
    app_activity: str = required_str_field(title="appActivity")
    template_device: int = Field(..., title="元素定位时参照的设备id")
    script_list: Optional[list[int]] = Field([], title="脚本文件")


class EditProjectForm(GetProjectForm, AddProjectForm):
    """ 修改app参数校验 """


class GetEnvForm(BaseForm):
    """ 查找app环境form """
    project_id: int = Field(..., title="项目id")
    env_id: int = Field(..., title="环境id")

    @field_validator('project_id', 'env_id')
    def validate_env_id(cls, value, info: ValidationInfo):
        if info.field_name == 'env_id':
            project_id = info.data["project_id"]
            env_data = ProjectEnv.get_first(project_id=project_id, env_id=value)
            if not env_data:  # 如果没有就插入一条记录， 并且自动同步当前APP已有的环境数据
                project_other_env = ProjectEnv.get_first(project_id=project_id)
                if project_other_env:
                    insert_env_data = project_other_env.to_dict()
                    insert_env_data["env_id"] = value
                else:
                    insert_env_data = {"env_id": value, "project_id": project_id}
                ProjectEnv.model_create(insert_env_data)
            setattr(cls, "env_data", env_data)
        return value


class EditEnv(GetEnvForm):
    """ 修改环境 """
    id: int = Field(..., title="环境数据id")
    variables: List[ValidateModel] = Field(title="变量")

    @field_validator('variables')
    def validate_variables(cls, value):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        all_variables = {variable.key: variable.value for variable in value if variable.key}
        variables = [variable.model_dump() for variable in value]
        cls.validate_variable_format(variables)  # 校验格式

        script_list = Project.query.with_entities(
            Project.script_list).filter(id=getattr(cls, 'env_data').project_id).first()
        all_func_name = Script.get_func_by_script_id(script_list)
        cls.validate_func(all_func_name, content=cls.dumps(variables))  # 校验引用的自定义函数
        cls.validate_variable(all_variables, cls.dumps(variables), "自定义变量")  # 校验变量
        setattr(cls, 'all_variables', all_variables)
        return value


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    project_id: int = Field(..., title="服务id")
    env_from: int = Field(..., title="环境数据源")
    env_to: list = required_str_field(title="要同步到环境")

    @field_validator('project_id')
    def validate_project_id(cls, value):
        project = cls.validate_data_is_exist("服务不存在", Project, id=value)
        setattr(cls, "project", project)
        return value

    @field_validator('env_from')
    def validate_env_from(cls, value):
        env_from_data = cls.validate_data_is_exist(
            "环境不存在", ProjectEnv, project_id=getattr(cls, 'project').id, env_id=value)
        setattr(cls, "env_from_data", env_from_data)
        return value

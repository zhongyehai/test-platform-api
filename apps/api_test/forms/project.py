# -*- coding: utf-8 -*-
from typing import Optional, Union, List

import requests
import validators
from flask import g
from pydantic import field_validator

from ...base_form import BaseForm, Field, PaginationForm, ValidateModel, HeaderModel, required_str_field
from ..model_factory import ApiProject as Project, ApiProjectEnv as ProjectEnv, ApiModule as Module, \
    ApiCaseSuite as CaseSuite, ApiTask as Task
from ...system.models.user import User
from ...assist.models.script import Script


class GetProjectListForm(PaginationForm):
    """ 查找服务form """
    name: Optional[str] = Field(None, title="服务名")
    manager: Optional[Union[int, str]] = Field(None, title="负责人")
    business_id: Optional[int] = Field(None, title="所属业务线")
    create_user: Optional[Union[int, str]] = Field(None, title="创建者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.business_id:  # 传了业务线id，就获取对应的业务线的服务
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
    """ 获取具体服务信息 """
    id: int = Field(..., title='服务id')

    @field_validator("id")
    def validate_id(cls, value):
        project = cls.validate_data_is_exist("服务不存在", Project, id=value)
        setattr(cls, "project", project)
        return value


class DeleteProjectForm(GetProjectForm):
    """ 删除服务 """

    @field_validator("id")
    def validate_id(cls, value):
        cls.validate_is_true(Project.is_can_delete(value), "不能删除别人负责的服务")
        cls.validate_is_false(
            Module.db.session.query(Module.id).filter(Module.project_id == value).first(), '服务下有模块,不允许删除')
        cls.validate_is_false(
            CaseSuite.db.session.query(CaseSuite.id).filter(CaseSuite.project_id == value).first(),
            '服务下有用例集,不允许删除')
        cls.validate_is_false(
            Task.db.session.query(Task.id).filter(Task.project_id == value).first(), '服务下有任务，不允许删除')
        return value


class AddProjectForm(BaseForm):
    """ 添加服务参数校验 """
    name: str = required_str_field(title="服务名称")
    manager: int = Field(..., title="负责人")
    business_id: int = Field(..., title="业务线")
    swagger: Optional[Union[str, None]] = Field(None, title="swagger地址")
    script_list: Optional[list[int]] = Field([], title="脚本文件")

    @field_validator("swagger")
    def validate_swagger(cls, value):
        """ 校验swagger地址是否正确 """
        if value:
            cls.validate_is_true(validators.url(value) is True, "swagger地址不正确，请输入正确地址")
            cls.validate_is_true("swagger-ui.htm" not in value, "请输入获取swagger数据的地址，不要输入swagger-ui地址")
        return value


class EditProjectForm(GetProjectForm, AddProjectForm):
    """ 修改服务参数校验 """


class GetEnvForm(BaseForm):
    """ 获取服务环境form """
    project_id: int = Field(..., title="服务id")
    env_id: int = Field(..., title="环境id")

    def depends_validate(self):
        env_data = ProjectEnv.get_first(project_id=self.project_id, env_id=self.env_id)
        if not env_data:  # 如果没有就插入一条记录， 并且自动同步当前服务已有的环境数据
            project_other_env = ProjectEnv.get_first(project_id=self.project_id)
            if project_other_env:
                insert_env_data = project_other_env.to_dict()
                insert_env_data["env_id"] = self.env_id
            else:
                insert_env_data = {"env_id": self.env_id, "project_id": self.project_id}
            ProjectEnv.model_create(insert_env_data)
            env_data = ProjectEnv.get_first(project_id=self.project_id, env_id=self.env_id)
        setattr(self, "env_data", env_data)


class EditEnv(GetEnvForm):
    """ 修改环境 """
    id: int = Field(..., title='环境数据id')
    host: str = required_str_field(title='域名')
    variables: List[ValidateModel] = Field(title="变量")
    headers: List[HeaderModel] = Field(title="头部信息")

    @field_validator('id')
    def validate_id(cls, value):
        project_env = cls.validate_data_is_exist("环境不存在", ProjectEnv, id=value)
        setattr(cls, 'project_env', project_env)
        return value

    @field_validator('host')
    def validate_host(cls, value):
        try:
            res = requests.get(value, timeout=5)
            if res.status_code > 500:
                raise
        except:
            raise ValueError(f"环境地址【{value}】不可访问，请确认")
        return value

    def depends_validate(self):
        self.validate_project_id()
        self.validate_variables()
        self.validate_headers()

    def validate_project_id(self):
        project = self.validate_data_is_exist("服务不存在", Project, id=self.project_id)
        all_func_name = Script.get_func_by_script_id(project.script_list)
        setattr(self, 'all_func_name', all_func_name)

    def validate_variables(self):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        all_variables = {variable.key: variable.value for variable in self.variables if variable.key}
        variables = [variable.model_dump() for variable in self.variables]
        self.validate_variable_format(variables)  # 校验格式
        self.validate_func(getattr(self, 'all_func_name'), content=self.dumps(variables))  # 校验引用的自定义函数
        self.validate_variable(all_variables, self.dumps(variables), "自定义变量")  # 校验变量
        setattr(self, 'all_variables', all_variables)

    def validate_headers(self):
        """ 头部参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        headers = [header.model_dump() for header in self.headers]
        self.validate_header_format(headers)  # 校验格式
        self.validate_func(getattr(self, 'all_func_name'), content=self.dumps(headers))  # 校验引用的自定义函数
        self.validate_variable(getattr(self, 'all_variables'), self.dumps(headers), "头部信息")  # 校验引用的变量


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    project_id: int = Field(..., title="服务id")
    env_from: int = Field(..., title="环境数据源")
    env_to: list = required_str_field(title="要同步到环境")

    def depends_validate(self):
        self.validate_project_id()
        self.validate_env_from()

    def validate_project_id(self):
        project = self.validate_data_is_exist("服务不存在", Project, id=self.project_id)
        setattr(self, "project", project)

    def validate_env_from(self):
        self.validate_project_id()
        env_from_data = self.validate_data_is_exist(
            "环境不存在", ProjectEnv, project_id=getattr(self, 'project').id, env_id=self.env_from)
        setattr(self, "env_from_data", env_from_data)

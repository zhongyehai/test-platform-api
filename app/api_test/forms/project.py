# -*- coding: utf-8 -*-
import validators
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from app.api_test.models.project import ApiProject as Project, ApiProjectEnv as ProjectEnv
from app.system.models.user import User
from app.assist.models.func import Func
from app.config.models.runEnv import RunEnv


class AddProjectForm(BaseForm):
    """ 添加服务参数校验 """
    name = StringField(validators=[DataRequired("服务名称不能为空"), Length(1, 255, message="服务名长度不可超过255位")])
    manager = StringField(validators=[DataRequired("请选择负责人")])
    business_id = StringField(validators=[DataRequired("请选择业务线")])
    num = StringField()
    swagger = StringField()
    func_files = StringField()

    def validate_name(self, field):
        """ 校验服务名不重复 """
        self.validate_data_is_not_exist(f"服务名【{field.data}】已存在", Project, name=field.data)

    def validate_manager(self, field):
        """ 校验服务负责人是否存在 """
        self.validate_data_is_exist(f"id为【{field.data}】的用户不存在", User, id=field.data)

    def validate_swagger(self, field):
        """ 校验swagger地址是否正确 """
        if field.data:
            self.validate_data_is_true(
                f"swagger地址不正确，请输入正确地址",
                validators.url(field.data) is True
            )
            self.validate_data_is_true(
                f"swagger地址不正确，请输入获取swagger数据的地址，不要输入swagger-ui地址",
                "swagger-ui.htm" not in field.data
            )


class FindProjectForm(BaseForm):
    """ 查找服务form """
    name = StringField()
    manager = StringField()
    create_user = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetProjectByIdForm(BaseForm):
    """ 获取具体服务信息 """
    id = IntegerField(validators=[DataRequired("服务id必传")])

    def validate_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的服务不存在", Project, id=field.data)
        setattr(self, "project", project)


class DeleteProjectForm(GetProjectByIdForm):
    """ 删除服务 """

    def validate_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的服务不存在", Project, id=field.data)
        self.validate_data_is_true("不能删除别人负责的服务", Project.is_can_delete(project.id, project))
        self.validate_data_is_false("请先去【接口管理】删除服务下的接口模块", project.modules)
        setattr(self, "project", project)


class EditProjectForm(GetProjectByIdForm, AddProjectForm):
    """ 修改服务参数校验 """

    def validate_name(self, field):
        """ 校验服务名不重复 """
        self.validate_data_is_not_repeat(
            f"服务名【{field.data}】已存在",
            Project,
            self.id.data,
            name=field.data
        )
        # old_project = ApiProject.get_first(name=field.data)
        # if old_project and old_project.name == field.data and old_project.id != self.id.data:
        #     raise ValidationError(f"服务名【{field.data}】已存在")


class AddEnv(BaseForm):
    """ 添加环境 """
    env_id = IntegerField(validators=[DataRequired("所属环境必传")])
    project_id = IntegerField(validators=[DataRequired("服务id必传")])
    host = StringField(validators=[DataRequired("域名必传")])
    variables = StringField()
    headers = StringField()
    all_func_name = {}

    def validate_project_id(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的服务不存在", Project, id=field.data)
        self.all_func_name = Func.get_func_by_func_file_name(self.loads(project.func_files), self.env_id.data)
        setattr(self, "project", project)

    def validate_host(self, field):
        if validators.url(field.data) is not True:
            raise ValidationError(f"环境地址【{field.data}】不正确，请输入正确的格式")

    def validate_variables(self, field):
        """ 校验公共变量 """
        # 校验格式
        self.validate_variable_format(field.data)

        # 校验存在使用自定义函数，但是没有引用函数文件的情况
        self.validate_func(self.all_func_name, self.dumps(field.data))

        # 校验存在使用自定义变量，但是没有声明的情况
        self.validate_variable({
            variable.get("key"): variable.get("value") for variable in field.data if variable.get("key")
        }, self.dumps(field.data))  # 公共变量

    def validate_headers(self, field):
        """ 校验头部信息是否有引用自定义函数 """
        # 校验格式
        self.validate_header_format(field.data)

        # 校验存在使用自定义函数，但是没有引用函数文件的情况
        self.validate_func(self.all_func_name, self.dumps(field.data))

        # 校验存在使用自定义变量，但是没有声明的情况
        self.validate_variable({
            variable.get("key"): variable.get("value") for variable in self.variables.data if variable.get("key")
        }, self.dumps(field.data))


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
    """ 查找服务环境form """
    projectId = IntegerField(validators=[DataRequired("服务id必传")])
    env_id = StringField()

    def validate_projectId(self, field):
        env_data = ProjectEnv.get_first(project_id=field.data, env_id=self.env_id.data)
        if not env_data:  # 如果没有就插入一条记录
            env_data = ProjectEnv().create({"env_id": self.env_id.data, "project_id": field.data})
            setattr(self, "env_data", env_data)
        setattr(self, "env_data", env_data)


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    projectId = IntegerField(validators=[DataRequired("服务id必传")])
    envFrom = StringField()
    envTo = StringField()

    def validate_projectId(self, field):
        project = self.validate_data_is_exist(f"id为【{field.data}】的服务不存在", Project, id=field.data)
        setattr(self, "project", project)

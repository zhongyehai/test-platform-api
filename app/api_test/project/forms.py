# -*- coding: utf-8 -*-
import validators
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from .models import ApiProject, ApiProjectEnv
from app.ucenter.user.models import User
from ..func.models import Func


class AddProjectForm(BaseForm):
    """ 添加服务参数校验 """
    name = StringField(validators=[DataRequired('服务名称不能为空'), Length(1, 255, message='服务名长度不可超过255位')])
    manager = StringField(validators=[DataRequired('请选择负责人')])
    swagger = StringField()

    def validate_name(self, field):
        """ 校验服务名不重复 """
        self.validate_data_is_not_exist(f'服务名【{field.data}】已存在', ApiProject, name=field.data)

    def validate_manager(self, field):
        """ 校验服务负责人是否存在 """
        self.validate_data_is_exist(f'id为【{field.data}】的用户不存在', User, id=field.data)

    def validate_swagger(self, field):
        """ 校验swagger地址是否正确 """
        if field.data:
            self.validate_data_is_true(
                f'swagger地址不正确，请输入正确地址',
                validators.url(field.data) is True
            )
            self.validate_data_is_true(
                f'swagger地址不正确，请输入获取swagger数据的地址，不要输入swagger-ui地址',
                'swagger-ui.htm' not in field.data
            )


class FindProjectForm(BaseForm):
    """ 查找服务form """
    name = StringField()
    manager = StringField()
    create_user = StringField()
    projectId = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetProjectByIdForm(BaseForm):
    """ 获取具体服务信息 """
    id = IntegerField(validators=[DataRequired('服务id必传')])

    def validate_id(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)
        setattr(self, 'project', project)


class DeleteProjectForm(GetProjectByIdForm):
    """ 删除服务 """

    def validate_id(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)
        self.validate_data_is_true('不能删除别人负责的服务', ApiProject.is_can_delete(project.id, project))
        self.validate_data_is_false('请先去【接口管理】删除服务下的接口模块', project.modules)
        setattr(self, 'project', project)


class EditProjectForm(GetProjectByIdForm, AddProjectForm):
    """ 修改服务参数校验 """

    def validate_name(self, field):
        """ 校验服务名不重复 """
        self.validate_data_is_not_repeat(
            f'服务名【{field.data}】已存在',
            ApiProject,
            self.id.data,
            name=field.data
        )
        # old_project = ApiProject.get_first(name=field.data)
        # if old_project and old_project.name == field.data and old_project.id != self.id.data:
        #     raise ValidationError(f'服务名【{field.data}】已存在')


class AddEnv(BaseForm):
    """ 添加环境 """
    project_id = IntegerField(validators=[DataRequired('服务id必传')])
    env = StringField(validators=[DataRequired('所属环境必传'), Length(1, 10, message='所属环境长度为1~10位')])
    host = StringField(validators=[DataRequired('域名必传'), Length(2, 255, message='域名长度为1~255位')])
    func_files = StringField()
    variables = StringField()
    headers = StringField()
    all_func_name = {}
    all_variables = {}

    def validate_project_id(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)
        setattr(self, 'project', project)

    def validate_host(self, field):
        """ 校验地址是否正确 """
        if field.data and validators.url(field.data) is not True:
            raise ValidationError(f'环境地址【{field.data}】不正确')

    def validate_func_files(self, field):
        """ 自定义函数文件 """
        self.all_func_name = Func.get_func_by_func_file_name(field.data)

    def validate_variables(self, field):
        """ 校验公共变量 """
        # 校验格式
        self.validate_variable_and_header_format(field.data, '自定义变量设置，，第【', '】行，要设置自定义变量，则key和value都需设置')

        # 校验存在使用自定义函数，但是没有引用函数文件的情况
        self.validate_func(self.all_func_name, self.dumps(field.data))

        # 校验存在使用自定义变量，但是没有声明的情况
        self.all_variables = {
            variable.get('key'): variable.get('value') for variable in field.data if variable.get('key')
        }
        self.validate_variable(self.all_variables, self.dumps(field.data))  # 公共变量

    def validate_headers(self, field):
        """ 校验头部信息是否有引用自定义函数 """
        # 校验格式
        self.validate_variable_and_header_format(field.data, '头部信息设置，第【', '】行，要设置头部信息，则key和value都需设置')

        # 校验存在使用自定义函数，但是没有引用函数文件的情况
        self.validate_func(self.all_func_name, self.dumps(field.data))

        # 校验存在使用自定义变量，但是没有声明的情况
        self.validate_variable(self.all_variables, self.dumps(field.data))


class EditEnv(AddEnv):
    """ 修改环境 """
    id = IntegerField(validators=[DataRequired('环境id必传')])

    def validate_env(self, field):
        env_data = self.validate_data_is_exist(
            '当前环境不存在',
            ApiProjectEnv,
            project_id=self.project_id.data,
            env=field.data
        )
        setattr(self, 'env_data', env_data)


class FindEnvForm(BaseForm):
    """ 查找服务环境form """
    projectId = IntegerField(validators=[DataRequired('服务id必传')])
    env = StringField()

    def validate_projectId(self, field):
        env_data = ApiProjectEnv.get_first(project_id=field.data, env=self.env.data)
        if not env_data:  # 如果没有就插入一条记录
            env_data = ApiProjectEnv().create({"env": self.env.data, "project_id": field.data})
            setattr(self, 'env_data', env_data)
        setattr(self, 'env_data', env_data)


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    projectId = IntegerField(validators=[DataRequired('服务id必传')])
    envFrom = StringField(validators=[DataRequired('所属环境必传'), Length(1, 10, message='所属环境长度为1~10位')])
    envTo = StringField(validators=[DataRequired('所属环境必传'), Length(1, 10, message='所属环境长度为1~10位')])

    def validate_projectId(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)
        setattr(self, 'project', project)

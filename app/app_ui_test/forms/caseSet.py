# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.app_ui_test.models.case import AppUiCase as Case
from app.app_ui_test.models.project import AppUiProject as Project
from app.app_ui_test.models.caseSet import AppUiCaseSet as CaseSet
from app.app_ui_test.models.env import AppUiRunServer as Server, AppUiRunPhone as Phone

class GetCaseSetForm(BaseForm):
    """ 获取用例集信息 """
    id = IntegerField(validators=[DataRequired("用例集id必传")])

    def validate_id(self, field):
        set = self.validate_data_is_exist(f"id为【{field.data}】的用例集不存在", CaseSet, id=field.data)
        setattr(self, "set", set)


class RunCaseSetForm(GetCaseSetForm):
    """ 运行用例集 """
    is_async = IntegerField()
    env_code = StringField(validators=[DataRequired("请选择运行环境")])
    server_id = IntegerField(validators=[DataRequired("请选择执行服务器")])
    phone_id = IntegerField(validators=[DataRequired("请选择执行手机")])

    def validate_id(self, field):
        set = self.validate_data_is_exist(f"id为【{field.data}】的用例集不存在", CaseSet, id=field.data)
        self.validate_data_is_exist(f"用例集下没有用例", Case, set_id=field.data)
        setattr(self, "set", set)

    def validate_server_id(self, field):
        """ 校验服务id存在 """
        server = self.validate_data_is_exist(f"id为【{field.data}】的服务器不存在", Server, id=field.data)
        setattr(self, "server", server)

    def validate_phone_id(self, field):
        """ 校验手机id存在 """
        phone = self.validate_data_is_exist(f"id为【{field.data}】的手机不存在", Phone, id=field.data)
        setattr(self, "phone", phone)


class AddCaseSetForm(BaseForm):
    """ 添加用例集的校验 """
    project_id = StringField(validators=[DataRequired("请先选择首页项目")])
    name = StringField(validators=[DataRequired("用例集名称不能为空"), Length(1, 255, message="用例集名长度为1~255位")])
    level = StringField()
    parent = StringField()
    id = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 项目id存在 """
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在，请先创建", Project, id=field.data)
        setattr(self, "project", project)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        self.validate_data_is_not_exist(
            f"用例集名字【{field.data}】已存在",
            CaseSet,
            project_id=self.project_id.data,
            level=self.level.data,
            name=field.data,
            parent=self.parent.data
        )


class GetCaseSetEditForm(BaseForm):
    """ 返回待编辑用例集合 """
    id = IntegerField(validators=[DataRequired("用例集id必传")])

    def validate_id(self, field):
        set = self.validate_data_is_exist("没有此用例集", CaseSet, id=field.data)
        setattr(self, "set", set)


class DeleteCaseSetForm(GetCaseSetEditForm):
    """ 删除用例集 """

    def validate_id(self, field):
        case_set = CaseSet.get_first(id=field.data)
        # 数据权限
        self.validate_data_is_true("不能删除别人项目下的用例集", Project.is_can_delete(case_set.project_id, case_set))

        # 用例集下是否有用例集
        self.validate_data_is_false("请先删除当前用例集下的用例集", CaseSet.get_first(parent=field.data))

        # 用例集下是否有用例
        self.validate_data_is_false("请先删除当前用例集下的用例", Case.get_first(set_id=field.data))

        setattr(self, "case_set", case_set)


class EditCaseSetForm(GetCaseSetEditForm, AddCaseSetForm):
    """ 编辑用例集 """

    def validate_id(self, field):
        """ 用例集id已存在 """
        case_set = self.validate_data_is_exist(f"不存在id为【{field.data}】的用例集", CaseSet, id=field.data)
        setattr(self, "case_set", case_set)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        self.validate_data_is_not_repeat(
            f"用例集名字【{field.data}】已存在",
            CaseSet,
            self.id.data,
            project_id=self.project_id.data,
            level=self.level.data,
            name=field.data,
            parent=self.parent.data
        )


class FindCaseSet(BaseForm):
    """ 查找用例集合 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    name = StringField()
    projectId = IntegerField(validators=[DataRequired("项目id必传")])

    def validate_projectId(self, field):
        self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)

# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.caseSuite import ApiCaseSuite as CaseSuite


class GetCaseSuiteForm(BaseForm):
    """ 获取用例集信息 """
    id = IntegerField(validators=[DataRequired("用例集id必传")])

    def validate_id(self, field):
        suite = self.validate_data_is_exist(f"id为【{field.data}】的用例集不存在", CaseSuite, id=field.data)
        setattr(self, "suite", suite)


class RunCaseSuiteForm(GetCaseSuiteForm):
    """ 运行用例集 """
    is_async = IntegerField()
    env_list = StringField(validators=[DataRequired("请选择运行环境")])

    def validate_id(self, field):
        suite = self.validate_data_is_exist(f"id为【{field.data}】的用例集不存在", CaseSuite, id=field.data)
        self.validate_data_is_exist(f"用例集下没有用例", Case, suite_id=field.data)
        setattr(self, "suite", suite)


class AddCaseSuiteForm(BaseForm):
    """ 添加用例集的校验 """
    name_length = CaseSuite.name.property.columns[0].type.length
    project_id = StringField(validators=[DataRequired("服务必传")])
    id = StringField()
    name = StringField(validators=[
        DataRequired("用例集名称不能为空"),
        Length(1, name_length, f"用例集名长度不可超过{name_length}位")
    ])
    suite_type = StringField(validators=[DataRequired("用例集类型必传")])
    parent = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 服务id合法 """
        project = self.validate_data_is_exist(f"id为【{field.data}】的服务不存在，请先创建", Project, id=field.data)
        setattr(self, "project", project)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        self.validate_data_is_not_exist(
            f"当前层级下，用例集名字【{field.data}】已存在",
            CaseSuite,
            project_id=self.project_id.data,
            name=field.data,
            parent=self.parent.data
        )


class DeleteCaseSuiteForm(GetCaseSuiteForm):
    """ 删除用例集 """

    def validate_id(self, field):
        suite = CaseSuite.get_first(id=field.data)
        # 数据权限
        self.validate_data_is_true("不能删除别人服务下的用例集", Project.is_can_delete(suite.project_id, suite))

        # 用例集下是否有用例集
        self.validate_data_is_false("请先删除当前用例集下的用例集", CaseSuite.get_first(parent=field.data))

        # 用例集下是否有用例
        self.validate_data_is_false("请先删除当前用例集下的用例", Case.get_first(suite_id=field.data))
        setattr(self, "suite", suite)


class EditCaseSuiteForm(GetCaseSuiteForm, AddCaseSuiteForm):
    """ 编辑用例集 """
    is_update_suite_type = False  # 判断是否修改了用例集类型

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        self.validate_data_is_not_repeat(
            f"用例集名字【{field.data}】已存在",
            CaseSuite,
            self.id.data,
            project_id=self.project_id.data,
            name=field.data,
            parent=self.parent.data
        )
        if self.parent.data is None and self.suite_type.data != self.suite.suite_type:
            self.is_update_suite_type = True


class FindCaseSuite(BaseForm):
    """ 查找用例集合 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    name = StringField()
    suite_type = StringField()
    project_id = IntegerField(validators=[DataRequired("服务id必传")])

    def validate_projectId(self, field):
        self.validate_data_is_exist(f"id为【{field.data}】的服务不存在", Project, id=field.data)

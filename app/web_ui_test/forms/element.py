# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired, ValidationError

from app.baseForm import BaseForm
from app.web_ui_test.models.element import WebUiElement as Element
from app.web_ui_test.models.page import WebUiPage as Page
from app.web_ui_test.models.module import WebUiModule as Module
from app.web_ui_test.models.project import WebUiProject as Project


class AddElementForm(BaseForm):
    """ 添加元素信息的校验 """
    project_id = StringField(validators=[DataRequired("项目id必传")])
    module_id = StringField(validators=[DataRequired("模块id必传")])
    page_id = StringField(validators=[DataRequired("页面id必传")])

    element_list = StringField(validators=[DataRequired("元素必传")])
    addr_lit = []

    def validate_project_id(self, field):
        """ 校验项目id """
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)
        setattr(self, "project", project)

    def validate_module_id(self, field):
        """ 校验模块id """
        self.validate_data_is_exist(f"id为【{field.data}】的模块不存在", Module, id=field.data)

    def validate_page_id(self, field):
        """ 校验页面id """
        self.validate_data_is_exist(f"id为【{field.data}】的页面不存在", Page, id=field.data)

    def validate_element_list(self, field):
        """ 校验元素信息 """
        name_list = []
        for index, element in enumerate(field.data):
            name, by, element = element.get("name"), element.get("by"), element.get("element")
            self.validate_data_is_true(f'第【{index + 1}】行，元素名必传', name)
            self.validate_data_is_true(f'第【{index + 1}】行，定位方式必传', by)
            self.validate_data_is_true(f'第【{index + 1}】行，元素表达式必传', element)
            if name in name_list:
                raise ValidationError(f'第【{index + 1}】行，与第【{name_list.index(name) + 1}】行，元素名重复')

            self.validate_data_is_not_exist(
                f"当前页面下，名为【{name}】的元素已存在",
                Element,
                name=name,
                page_id=self.page_id.data
            )
            if by == "url":
                self.addr_lit.append(element)

    def update_page_addr(self):
        """ 如果元素是页面地址，则同步修改页面表里面对应的地址 """
        if len(self.addr_lit) > 0:
            page = Page.get_first(id=self.page_id.data)
            page.update({"addr": self.addr_lit[0]})


class EditElementForm(AddElementForm):
    """ 修改元素信息 """
    element_list = None

    id = IntegerField(validators=[DataRequired("元素id必传")])

    name = StringField(validators=[DataRequired("元素名字必传"), Length(1, 255, "元素名字长度为1~255位")])
    by = StringField(validators=[DataRequired("定位方式必传"), Length(1, 255, "定位方式长度为1~255位")])
    element = StringField(validators=[DataRequired("定位元素表达式必传")])
    desc = StringField()
    num = StringField()
    wait_time_out = IntegerField()

    def validate_id(self, field):
        """ 校验元素id已存在 """
        old = self.validate_data_is_exist(f"id为【{field.data}】的元素不存在", Element, id=field.data)
        setattr(self, "old", old)

    def validate_name(self, field):
        """ 校验元素名不重复 """
        self.validate_data_is_not_repeat(
            f"当前页面下，名为【{field.data}】的元素已存在",
            Element,
            self.id.data,
            name=field.data,
            page_id=self.page_id.data
        )

    def validate_by(self, field):
        """ 一个页面只能有一个url地址 """
        if field.data == "url":
            self.validate_data_is_not_repeat(
                f"一个页面只能有一个地址",
                Element,
                self.id.data,
                page_id=self.page_id.data,
                by="url"
            )
            self.addr_lit.append(self.element.data)


class ValidateProjectId(BaseForm):
    """ 校验项目id """
    projectId = IntegerField(validators=[DataRequired("项目id必传")])

    def validate_projectId(self, field):
        """ 校验项目id """
        self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)


class ChangeElementById(BaseForm):
    """ 根据id更新元素 """
    id = IntegerField(validators=[DataRequired("元素id必传")])
    by = StringField(validators=[DataRequired("定位方式必传"), Length(1, 255, "定位方式长度为1~255位")])
    element = StringField(validators=[DataRequired("定位元素表达式必传")])

    def validate_id(self, field):
        """ 校验元素id已存在 """
        old = self.validate_data_is_exist(f"id为【{field.data}】的元素不存在", Element, id=field.data)
        setattr(self, "old", old)


class ElementListForm(BaseForm):
    """ 查询接口信息 """
    pageId = IntegerField(validators=[DataRequired("请选择页面")])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetElementById(BaseForm):
    """ 待编辑信息 """
    id = IntegerField(validators=[DataRequired("元素id必传")])

    def validate_id(self, field):
        element = self.validate_data_is_exist(f"id为【{field.data}】的元素不存在", Element, id=field.data)
        setattr(self, "element", element)


class DeleteElementForm(GetElementById):
    """ 删除元素 """

    def validate_id(self, field):
        element = self.validate_data_is_exist(f"id为【{field.data}】的元素不存在", Element, id=field.data)
        self.validate_data_is_true("不能删除别人项目下的元素", Project.is_can_delete(element.project_id, element))
        setattr(self, "element", element)

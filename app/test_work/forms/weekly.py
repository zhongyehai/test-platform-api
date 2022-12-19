# -*- coding: utf-8 -*-
from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from app.baseForm import BaseForm
from ..models.weekly import WeeklyModel, WeeklyConfigModel


class GetWeeklyConfigListForm(BaseForm):
    """ 获取产品、项目列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    name = StringField()
    parent = StringField()

    def validate_parent(self, field):
        self.parent.data = "null" if not field.data else field.data


class GetWeeklyConfigForm(BaseForm):
    """ 获取产品、项目 """
    id = IntegerField(validators=[DataRequired("产品或项目id必传")])

    def validate_id(self, field):
        conf = self.validate_data_is_exist(f"id为 {field.data} 的产品或项目不存在", WeeklyConfigModel, id=field.data)
        setattr(self, "conf", conf)


class DeleteWeeklyConfigForm(GetWeeklyConfigForm):
    """ 删除产品、项目 """
    id = IntegerField(validators=[DataRequired("配置类型id必传")])

    def validate_id(self, field):
        conf = self.validate_data_is_exist(f"id为 {field.data} 的配置不存在", WeeklyConfigModel, id=field.data)
        if not conf.parent:  # 产品
            self.validate_data_is_not_exist("当前产品下还有项目，请先删除项目", WeeklyConfigModel, parent=field.data)  # 判断产品下无项目
            self.validate_data_is_not_exist("当前产品下还有周报，请先删除周报", WeeklyModel, product_id=field.data)  # 判断产品下无周报
        else:  # 项目
            self.validate_data_is_not_exist("当前项目下还有周报，请先删除周报", WeeklyModel, project_id=field.data)  # 判断项目下无周报
        setattr(self, "conf", conf)


class AddWeeklyConfigForm(BaseForm):
    """ 添加产品、项目 """
    name = StringField(validators=[DataRequired("请输入名称")])
    parent = StringField()
    desc = StringField()

    def validate_name(self, field):
        """ 校验名字不重复 """
        if self.parent.data:  # 有父级，为项目
            self.validate_data_is_not_exist(
                f"当前节点下已存在名为【{field.data}】的项目",
                WeeklyConfigModel,
                name=field.data,
                parent=self.parent.data
            )
        else:  # 没有父级，为产品
            self.validate_data_is_not_exist(
                f"已存在名为【{field.data}】的产品",
                WeeklyConfigModel,
                name=field.data,
                parent=None
            )


class ChangeWeeklyConfigForm(GetWeeklyConfigForm, AddWeeklyConfigForm):
    """ 修改产品、项目 """

    def validate_name(self, field):
        """ 校验名字不重复 """
        if self.parent.data:  # 产品
            self.validate_data_is_not_repeat(
                f"已存在名为【{field.data}】的产品",
                WeeklyConfigModel,
                self.conf.id,
                name=field.data,
                parent=None
            )
        else:  # 项目
            self.validate_data_is_not_repeat(
                f"当前产品下已存在名为【{field.data}】的项目",
                WeeklyConfigModel,
                self.conf.id,
                name=field.data,
                parent=self.parent.data
            )


class GetWeeklyListForm(BaseForm):
    """ 获取周报列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    product_id = StringField()
    project_id = StringField()
    version = StringField()
    task_item = StringField()
    start_time = StringField()
    end_time = StringField()
    create_user = StringField()
    download_type = StringField()


class GetWeeklyForm(BaseForm):
    """ 获取周报 """
    id = IntegerField(validators=[DataRequired("周报id必传")])

    def validate_id(self, field):
        weekly = self.validate_data_is_exist(f"id为 {field.data} 的周报不存在", WeeklyModel, id=field.data)
        setattr(self, "weekly", weekly)


class DeleteWeeklyForm(GetWeeklyForm):
    """ 删除周报 """


class AddWeeklyForm(BaseForm):
    """ 添加周报 """
    product_id = StringField()
    project_id = StringField()
    version = StringField(validators=[DataRequired("请输入版本号")])
    task_item = StringField(validators=[DataRequired("请输入任务明细")])
    desc = StringField()
    start_time = StringField()
    end_time = StringField()

    def validate_product_id(self, field):
        """ 校验产品id或者项目id必须存在 """
        if field.data:
            self.validate_data_is_exist(f"id为【{field.data}】的产品不存在", WeeklyConfigModel, id=field.data)
        elif self.project_id.data:
            self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", WeeklyConfigModel, id=self.project_id.data)
        else:
            raise ValidationError("请选择产品或者项目")

    def validate_task_item(self, field):
        """ 校验任务明细必须有值：[{"item": "xxx", "progress": "50%"}] """
        task_item_container = []
        for index, data in enumerate(field.data):
            key, value = data.get("key", ""), data.get("value", "")
            if key and value:
                task_item_container.append(index)
            elif key and not value:
                raise ValidationError(f"任务明细第【{index + 1}】项，测试进度未填写")
            elif value and not key:
                raise ValidationError(f"任务明细第【{index + 1}】项，测试任务未填写")
        if not task_item_container:
            raise ValidationError("请完善测试任务明细")

    def validate_start_time(self, field):
        """ 同一个产品，同一个项目，同一个版本号，同一个人，同一周只能有一条数据 """
        self.validate_data_is_not_exist(
            "你已经填写过当前时间段在当前项目的周报",
            WeeklyModel,
            product_id=self.product_id.data,
            project_id=self.project_id.data,
            version=self.version.data.strip(),
            start_time=field.data,
            create_user=g.user_id
        )


class ChangeWeeklyForm(GetWeeklyForm, AddWeeklyForm):
    """ 修改周报 """

    def validate_start_time(self, field):
        """ 同一个产品，同一个项目，同一个版本号，同一个人，同一周只能有一条数据 """
        self.validate_data_is_not_repeat(
            "你已经填写过当前时间段在当前项目的周报",
            WeeklyModel,
            self.weekly.id,
            product_id=self.product_id.data,
            project_id=self.project_id.data,
            version=self.version.data.strip(),
            start_time=field.data,
            create_user=g.user_id
        )

from typing import Optional, Union

from pydantic import Field, field_validator, ValidationInfo
from sqlalchemy import or_

from ...base_form import BaseForm, PaginationForm
from ..model_factory import WeeklyModel, WeeklyConfigModel


class GetWeeklyConfigListForm(PaginationForm):
    """ 获取产品、项目列表 """
    name: Optional[str] = Field(None, title="名字")
    parent: Optional[str] = Field(None, title="父级")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(WeeklyConfigModel.name.like(f'{self.name}'))
        if self.parent:
            filter_list.append(WeeklyConfigModel.parent == self.parent)

        return filter_list


class GetWeeklyConfigForm(BaseForm):
    """ 获取产品、项目 """
    id: int = Field(..., title="bug数据id")

    @field_validator("id")
    def validate_id(cls, value):
        conf = cls.validate_data_is_exist("数据不存在", WeeklyConfigModel, id=value)
        setattr(cls, "conf", conf)
        return value


class DeleteWeeklyConfigForm(GetWeeklyConfigForm):
    """ 删除产品、项目 """

    @field_validator("id")
    def validate_id(cls, value):
        data_query = WeeklyConfigModel.db.session.query(WeeklyConfigModel.create_user).filter(or_(
            WeeklyConfigModel.parent == value, WeeklyModel.product_id == value, WeeklyModel.project_id == value
        )).first()
        cls.validate_is_false(data_query, '当前产品下还有项目 或 当前产品下还有周报 或 当前项目下还有周报')
        return value


class AddWeeklyConfigForm(BaseForm):
    """ 添加产品、项目 """
    name: int = Field(..., title="名称")
    parent: Optional[int] = Field(title="父级")
    desc: Optional[str] = Field(title="描述")


class ChangeWeeklyConfigForm(GetWeeklyConfigForm, AddWeeklyConfigForm):
    """ 修改产品、项目 """


class GetWeeklyListForm(PaginationForm):
    """ 获取周报列表 """
    product_id: Optional[int] = Field(None, title="产品id")
    project_id: Optional[int] = Field(None, title="项目id")
    create_user: Optional[int] = Field(None, title="创建人")
    version: Optional[str] = Field(None, title="版本")
    task_item: Optional[str] = Field(None, title="任务明细")
    start_time: Optional[str] = Field(None, title="开始时间")
    end_time: Optional[str] = Field(None, title="结束时间")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.product_id:
            filter_list.append(WeeklyModel.product_id == self.product_id)
        if self.project_id:
            filter_list.append(WeeklyModel.project_id == self.project_id)
        if self.version:
            filter_list.append(WeeklyModel.version == self.version)
        if self.task_item:
            filter_list.append(WeeklyModel.task_item.like(f'{self.version}'))
        if self.start_time:
            filter_list.append(WeeklyModel.start_time >= self.start_time)
        if self.end_time:
            filter_list.append(WeeklyModel.end_time < self.end_time)
        if self.create_user:
            filter_list.append(WeeklyModel.create_user == self.create_user)
        return filter_list


class GetWeeklyForm(BaseForm):
    """ 获取周报 """
    id: int = Field(..., title="周报id")

    @field_validator("id")
    def validate_id(cls, value):
        weekly = cls.validate_data_is_exist("数据不存在", WeeklyModel, id=value)
        setattr(cls, "weekly", weekly)
        return value


class DeleteWeeklyForm(GetWeeklyForm):
    """ 删除周报 """


class DownloadWeeklyForm(GetWeeklyForm):
    download_type: Optional[Union[str, None]] = Field(title="下载时间段类型")


class AddWeeklyForm(BaseForm):
    """ 添加周报 """
    product_id: Optional[int] = Field(title="产品id")
    project_id: Optional[int] = Field(title="项目id")
    version: str = Field(..., title="版本号")
    task_item: str = Field(..., title="任务明细")
    desc: Optional[str] = Field(title="备注")
    start_time: Optional[str] = Field(title="开始时间")
    end_time: Optional[str] = Field(title="结束时间")

    @field_validator("project_id")
    def validate_project_id(cls, value, info: ValidationInfo):
        """ 校验产品id或者项目id必须存在 """
        cls.validate_is_true(value or info.data["product_id"], '请选择产品或者项目')
        return value

    @field_validator("task_item")
    def validate_task_item(cls, value):
        """ 校验任务明细必须有值：[{"item": "xxx", "progress": "50%"}] """
        task_item_container = []
        for index, data in enumerate(value):
            key, value = data.get("key", ""), data.get("value", "")
            if key and value:
                task_item_container.append(index)
            elif key and not value:
                raise ValueError(f"任务明细第【{index + 1}】项，测试进度未填写")
            elif value and not key:
                raise ValueError(f"任务明细第【{index + 1}】项，测试任务未填写")
        if not task_item_container:
            raise ValueError("请完善测试任务明细")
        return value


class ChangeWeeklyForm(GetWeeklyForm, AddWeeklyForm):
    """ 修改周报 """

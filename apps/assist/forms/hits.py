from typing import Optional

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import Hits


class GetHitListForm(PaginationForm):
    """ 获取自动化测试命中问题列表 """
    date: Optional[str] = Field(None, title='记录时间')
    hit_type: Optional[str] = Field(None, title='问题类型')
    test_type: Optional[str] = Field(None, title='测试类型')
    hit_detail: Optional[str] = Field(None, title='问题内容')
    report_id: Optional[int] = Field(None, title='报告id')
    record_from: Optional[int] = Field(None, title='数据记录的来源', description='数据记录的来源，1、人为/2、自动')

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.date:
            filter_list.append(Hits.date == self.date)
        if self.hit_type:
            filter_list.append(Hits.hit_type == self.hit_type)
        if self.test_type:
            filter_list.append(Hits.test_type == self.test_type)
        if self.report_id:
            filter_list.append(Hits.report_id == self.report_id)
        if self.record_from:
            filter_list.append(Hits.record_from == self.record_from)
        if self.hit_detail:
            filter_list.append(Hits.hit_detail.like(f'%{self.hit_detail}%'))
        return filter_list


class GetHitForm(BaseForm):
    """ 获取自定义自动化测试命中问题 """
    id: int = Field(..., title="数据id")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验自定义自动化测试命中问题需存在 """
        hit = cls.validate_data_is_exist('数据不存在', Hits, id=value)
        setattr(cls, "hit", hit)
        return value


class CreatHitForm(BaseForm):
    """ 创建自定义自动化测试命中问题 """
    date: str = required_str_field(title='问题触发日期')
    hit_type: str = required_str_field(title='问题类型')
    test_type: str = required_str_field(title='测试类型')
    hit_detail: str = required_str_field(title='问题内容')
    env: str = required_str_field(title='环境')
    project_id: int = Field(..., title='服务id')
    report_id: int = Field(..., title='测试报告id')
    desc: Optional[str] = Field(None, title='描述')

    @field_validator("date")
    def validate_date(cls, value):
        return value[0:10]


class EditHitForm(GetHitForm, CreatHitForm):
    """ 修改自定义自动化测试命中问题 """

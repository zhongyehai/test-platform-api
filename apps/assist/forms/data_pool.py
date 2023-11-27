from typing import Optional

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm
from ..model_factory import DataPool, AutoTestUser


class GetAutoTestUserDataListForm(PaginationForm):
    """ 获取自动化用户数据 """
    env: Optional[str] = Field(None, title="环境")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.env:
            filter_list.append(AutoTestUser.env == self.env)
        return filter_list


class GetDataPoolListForm(PaginationForm):
    """ 获取数据池列表/新增数据池数据 """
    env: Optional[str] = Field(None, title="环境")
    mobile: Optional[str] = Field(None, title="手机号")
    business_order_no: Optional[str] = Field(None, title="订单号")
    business_status: Optional[str] = Field(None, title="业务状态")
    use_status: Optional[str] = Field(None, title="使用状态")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.env:
            filter_list.append(DataPool.env.like(f'%{self.env}%'))
        if self.mobile:
            filter_list.append(DataPool.env.like(f'%{self.mobile}%'))
        if self.business_order_no:
            filter_list.append(DataPool.env.like(f'%{self.business_order_no}%'))
        if self.business_status:
            filter_list.append(DataPool.env.like(f'%{self.business_status}%'))
        if self.use_status:
            filter_list.append(DataPool.env.like(f'%{self.use_status}%'))
        return filter_list


class GetDataPoolForm(BaseForm):
    """ 校验数据池数据存在 """
    id: int = Field(..., title="数据id")

    @field_validator("id")
    def validate_id(cls, value):
        data_pool = cls.validate_data_is_exist('数据不存在', DataPool, id=value)
        setattr(cls, "data_pool", data_pool)
        return value


class DeleteDataPoolForm(GetDataPoolForm):
    """ 删除数据池数据 """


class PostDataPoolForm(BaseForm):
    """ 新增数据池数据 """
    env: str = Field(..., title="环境")
    desc: Optional[str] = Field(None, title="描述文字")
    mobile: Optional[str] = Field(None, title="手机号")
    password: Optional[str] = Field(None, title="密码")
    business_order_no: str = Field(..., title="流水号")
    amount: Optional[str] = Field(None, title="金额")
    business_status: str = Field(..., title="业务状态")
    use_status: str = Field(..., title="使用状态")


class PutDataPoolForm(GetDataPoolForm, PostDataPoolForm):
    """ 修改数据池数据 """

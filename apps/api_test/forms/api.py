# -*- coding: utf-8 -*-
from typing import Optional, List, Union

from pydantic import field_validator

from ...base_form import BaseForm, PaginationForm, Field, HeaderModel, ParamModel, DataFormModel, ExtractModel, \
    ValidateModel, required_str_field, ApiListModel
from ..model_factory import ApiCase as Case, ApiStep as Step, ApiMsg as Api
from ...enums import ApiMethodEnum, ApiBodyTypeEnum, DataStatusEnum


class ApiListForm(PaginationForm):
    """ 查询接口信息 """
    module_id: int = Field(..., title="模块id")
    name: Optional[str] = Field(None, title="接口名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Api.module_id == self.module_id]
        if self.name:
            filter_list.append(Api.name.like(f'%{self.name}%'))
        return filter_list


class GetApiForm(BaseForm):
    """ 获取api信息 """
    id: int = Field(..., title="接口id")

    @field_validator('id')
    def validate_id(cls, value):
        api = cls.validate_data_is_exist("接口不存在", Api, id=value)
        setattr(cls, 'api', api)
        return value


class DeleteApiForm(GetApiForm):
    """ 删除接口 """

    @field_validator('id')
    def validate_id(cls, value):
        case_name = Api.db.session.query(Case.name).filter(Step.api_id == value).filter(Case.id == Step.case_id).first()
        if case_name:
            raise ValueError(f"用例【{case_name[0]}】已引用此接口，请先解除引用")
        return value


class AddApiForm(BaseForm):
    """ 添加接口信息的校验 """
    project_id: int = Field(..., title="服务id")
    module_id: int = Field(..., title="模块id")
    api_list: List[ApiListModel] = Field(..., title="接口列表")

    def depends_validate(self):
        api_data_list = [{
            "project_id": self.project_id, "module_id": self.module_id, **api.model_dump()
        } for api in self.api_list]
        self.api_list = api_data_list


class EditApiForm(GetApiForm):
    """ 修改接口信息 """
    addr: str = required_str_field(title="接口地址")
    extracts: List[ExtractModel] = Field(title="提取信息")
    validates: List[ValidateModel] = Field(title="断言信息")
    project_id: int = Field(..., title="服务id")
    module_id: int = Field(..., title="模块id")
    name: str = required_str_field(title="接口名")
    desc: Optional[str] = Field(None, title="备注")
    up_func: Optional[list] = Field([], title="前置条件")
    down_func: Optional[list] = Field([], title="后置条件")
    method: ApiMethodEnum = Field(ApiMethodEnum.GET.value, title="请求方法")
    headers: List[HeaderModel] = Field(title="头部信息")
    params: List[ParamModel] = Field(title="url参数")
    body_type: ApiBodyTypeEnum = Field(
        ApiBodyTypeEnum.json.value, title="请求体数据类型", description="json/form/text/urlencoded")
    data_form: List[DataFormModel] = Field(title="data-form参数")
    data_json: Union[list, dict] = Field({}, title="json参数")
    data_urlencoded: Union[list, dict] = Field(title="urlencoded参数")
    data_text: Optional[str] = Field(title="文本参数")
    time_out: Optional[int] = Field(title="请求超时时间")
    response: Optional[Union[str, dict, list]] = Field({}, title="接口响应")
    mock_response: Optional[Union[str, dict, list]] = Field({}, title="mock接口响应")

    @field_validator('headers')
    def validate_headers(cls, value):
        """ 头部信息校验 """
        cls.validate_header_format([header.model_dump() for header in value], content_title='头部信息')
        return value

    @field_validator('params')
    def validate_params(cls, value):
        """ params信息校验 """
        cls.validate_header_format([params.model_dump() for params in value], content_title='url参数')
        return value

    @field_validator('addr')
    def validate_addr(cls, value):
        """ 接口地址校验 """
        cls.validate_is_true(value.split("?")[0], "接口地址不能为空")
        return value

    @field_validator('extracts')
    def validate_extracts(cls, value):
        """ 校验提取数据表达式 """
        cls.validate_api_extracts([extract.model_dump() for extract in value])
        return value

    @field_validator('validates')
    def validate_validates(cls, value):
        """ 校验断言表达式 """
        cls.validate_base_validates([validate.model_dump() for validate in value])
        return value

    def depends_validate(self):
        data_form_value = [data_form.model_dump() for data_form in self.data_form]
        if self.body_type == ApiBodyTypeEnum.form.value:
            self.validate_variable_format(data_form_value, msg_title='form-data')
        return data_form_value


class GetApiFromForm(BaseForm):
    """ 查询api归属 """
    id: Optional[str] = Field(None, title="接口id")
    api_addr: Optional[str] = Field(None, title="接口地址")

    def depends_validate(self):
        if self.id:
            self.validate_data_is_exist("接口不存在", Api, id=self.id)
            setattr(self, 'api_id_list', [self.id])
        else:
            self.validate_is_true(self.api_addr, "请传入接口地址或接口id")
            api_id_list = Api.db.session.query(Api.id).filter(Api.addr.like(f"%{self.api_addr}%")).all()
            setattr(self, 'api_id_list', [api_id[0] for api_id in api_id_list])


class ChangeLevel(GetApiForm):
    level: str = required_str_field(title="接口等级", description="P0、P1、P2")


class ChangeStatus(GetApiForm):
    status: DataStatusEnum = Field(..., title="接口状态", description="此接口状态，enable/disable")

    @field_validator('id')
    def validate_id(cls, value):
        return value


class RunApiMsgForm(BaseForm):
    """ 运行接口 """
    id_list: list = required_str_field(title="要运行的接口id")
    env_list: List[str] = required_str_field(title="运行环境code")

    @field_validator("id_list")
    def validate_id_list(cls, value):
        run_api_id_list_query = Api.db.session.query(Api.id).filter(Api.id.in_(value)).all()
        run_api_id_list = [query[0] for query in run_api_id_list_query]
        cls.validate_is_true(run_api_id_list, '接口不存在')
        api_query = Api.db.session.query(Api.name, Api.project_id).filter(Api.id == run_api_id_list[0]).first()
        setattr(cls, 'run_api_id_list', run_api_id_list)
        setattr(cls, 'api_name', api_query[0])
        setattr(cls, 'project_id', api_query[1])
        return value

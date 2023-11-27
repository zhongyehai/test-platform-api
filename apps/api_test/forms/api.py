# -*- coding: utf-8 -*-
from typing import Optional, List, Union

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from ...base_form import BaseForm, PaginationForm, Field, HeaderModel, ParamModel, DataFormModel, ExtractModel, \
    ValidateModel
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
    addr: str = Field(..., title="接口地址")
    extracts: List[ExtractModel] = Field(title="提取信息")
    validates: List[ValidateModel] = Field(title="断言信息")
    data_form: List[DataFormModel] = Field(title="data-form参数")
    project_id: int = Field(..., title="服务id")
    module_id: int = Field(..., title="模块id")
    name: str = Field(..., title="接口名")
    desc: Optional[str] = Field(title="备注")
    up_func: Optional[list] = Field([], title="前置条件")
    down_func: Optional[list] = Field([], title="后置条件")
    method: ApiMethodEnum = Field(ApiMethodEnum.GET.value, title="请求方法")
    headers: List[HeaderModel] = Field(title="头部信息")
    params: List[ParamModel] = Field(title="url参数")
    body_type: ApiBodyTypeEnum = Field(
        ApiBodyTypeEnum.json.value, title="请求体数据类型", description="json/form/text/urlencoded")
    data_json: Union[list, dict] = Field(title="json参数")
    data_urlencoded: dict = Field(title="urlencoded参数")
    data_text: Optional[str] = Field(title="文本参数")
    time_out: Optional[int] = Field(title="请求超时时间")

    @field_validator('addr')
    def validate_addr(cls, value):
        """ 接口地址校验 """
        cls.validate_is_true("接口地址不能为空", value.split("?")[0])
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

    @field_validator('data_form')
    def validate_data_form(cls, value):
        cls.validate_variable_format([data_form.model_dump() for data_form in value], msg_title='form-data')
        return value

    @field_validator('module_id', 'name')
    def validate_name(cls, value, info: ValidationInfo):
        if info.field_name == 'name':
            cls.validate_data_is_not_exist(
                f"当前模块下，名为【{value}】的接口已存在", Api, name=value, module_id=info.data["module_id"])
        return value


class EditApiForm(AddApiForm, GetApiForm):
    """ 修改接口信息 """

    @field_validator('id', 'module_id', 'name')
    def validate_name(cls, value, info: ValidationInfo):
        if info.field_name == 'id':
            api = cls.validate_data_is_exist("接口不存在", Api, id=value)
            setattr(cls, 'api', api)
        elif info.field_name == 'name':
            cls.validate_data_is_not_repeat(
                f"当前模块下，名为【{value}】的接口已存在",
                Api, info.data["id"], name=value, module_id=info.data["module_id"]
            )
        return value


class GetApiFromForm(BaseForm):
    """ 查询api归属 """
    id: Optional[str] = Field(None, title="接口id")
    addr: Optional[str] = Field(None, title="接口地址")

    @field_validator("id")
    def validate_api_id(cls, value):
        cls.validate_data_is_exist("接口不存在", Api, id=value)
        setattr(cls, 'api_id_list', [value])
        return value

    @field_validator("addr")
    def validate_addr(cls, value, info: ValidationInfo):
        if not info.data["id"]:
            cls.validate_is_true(value, "请传入接口地址或接口id")
            api_id_list = Api.db.session.query(Api.id).filter(Api.addr.like(f"%{value}%")).all()
            setattr(cls, 'api_id_list', [api_id[0] for api_id in api_id_list])
        return value


class ChangeLevel(GetApiForm):
    level: str = Field(..., title="接口等级", description="P0、P1、P2")


class ChangeStatus(GetApiForm):
    status: DataStatusEnum = Field(..., title="接口状态", description="此接口状态，enable/disable")

    @field_validator('id')
    def validate_id(cls, value):
        return value


class RunApiMsgForm(BaseForm):
    """ 运行接口 """
    api_list: List[int] = Field(..., title="要运行的接口id")
    env_list: List[str] = Field(..., title="运行环境code")

    @field_validator("api_list")
    def validate_api_list(cls, value):
        run_api_id_list_query = Api.db.session.query(Api.id).filter(Api.id.in_(value)).all()
        run_api_id_list = [query[0] for query in run_api_id_list_query]
        cls.validate_is_true(run_api_id_list, '接口不存在')
        api_query = Api.db.session.query(Api.name, Api.project_id).filter(Api.id == run_api_id_list[0]).first()
        setattr(cls, 'run_api_id_list', run_api_id_list)
        setattr(cls, 'api_name', api_query[0])
        setattr(cls, 'project_id', api_query[1])
        return value

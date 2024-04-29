from typing import List

from pydantic import Field, field_validator, BaseModel as pydanticBaseModel
from ...base_form import BaseForm, required_str_field
from ..model_factory import Todo


class GetTodoForm(BaseForm):
    id: int = Field(..., title="数据id")

    @field_validator("id")
    def validate_id(cls, value):
        todo = cls.validate_data_is_exist("数据不存在", Todo, id=value)
        setattr(cls, "todo", todo)
        return value


class DeleteTodoForm(GetTodoForm):
    """ 删除数据 """


class ChangeStatusForm(GetTodoForm):
    status: str = required_str_field(title="状态")


class TodoForm(pydanticBaseModel):
    # tags: str = Field(None, title="tags")
    title: str = required_str_field(title="任务title")
    detail: str = required_str_field(title="任务详情")


class AddTodoForm(BaseForm):
    """ 添加数据 """
    data_list: List[TodoForm] = Field()

    @field_validator("data_list")
    def validate_data_list(cls, value):
        todo_list = []
        for index, item in enumerate(value):
            cls.validate_is_true(item.title and item.detail, f"第 {index} 行，请完善数据")
            todo_list.append({"title": item.title, "detail": item.detail})
        return todo_list


class ChangeTodoForm(GetTodoForm, TodoForm):
    """ 修改数据 """

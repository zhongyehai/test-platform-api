# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.system.models.user import Role, UserRoles


class GetRoleForm(BaseForm):
    """ 获取具体角色 """
    id = IntegerField(validators=[DataRequired("角色id必传")])

    def validate_id(self, field):
        role = self.validate_data_is_exist(f"没有id为 {field.data} 的角色", Role, id=field.data)
        setattr(self, "role", role)


class CreateRoleForm(BaseForm):
    """ 创建角色的验证 """
    name_length = Role.name.property.columns[0].type.length
    desc_length = Role.desc.property.columns[0].type.length
    name = StringField(
        validators=[DataRequired("请设置角色名"), Length(1, name_length, message=f"角色名长度不超过{name_length}位")])
    desc = StringField(validators=[Length(0, desc_length, message=f"备注名长度不超过{desc_length}位")])
    extend_role = StringField()
    api_permission = StringField()
    front_permission = StringField()

    def validate_name(self, field):
        """ 角色名不重复 """
        self.validate_data_is_not_exist(f"角色名 {field.data} 已存在", Role, name=field.data)


class FindRoleForm(BaseForm):
    """ 查找角色参数校验 """
    name = StringField()
    role_id = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class DeleteRoleForm(GetRoleForm):
    """ 删除角色 """

    def validate_id(self, field):
        """ 如果角色被角色使用了，则不能删除 """
        role = self.validate_data_is_exist(f"没有id为 {field.data} 的角色", Role, id=field.data)
        self.validate_data_is_not_exist(f"角色已被用户引用，请先解除引用", UserRoles, role_id=field.data)
        setattr(self, "role", role)


class EditRoleForm(GetRoleForm, CreateRoleForm):
    """ 编辑角色的校验 """

    def validate_name(self, field):
        """ 校验角色名不重复 """
        self.validate_data_is_not_repeat(
            f"角色名 {field.data} 已存在",
            Role,
            self.id.data,
            name=field.data
        )

# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.system.models.user import Permission, RolePermissions


class GetPermissionForm(BaseForm):
    """ 获取具体权限 """
    id = IntegerField(validators=[DataRequired("权限id必传")])

    def validate_id(self, field):
        permission = self.validate_data_is_exist(f"没有id为 {field.data} 的权限", Permission, id=field.data)
        setattr(self, "permission", permission)


class CreatePermissionForm(BaseForm):
    """ 创建权限的验证 """
    name_length = Permission.name.property.columns[0].type.length
    desc_length = Permission.desc.property.columns[0].type.length
    source_addr_length = Permission.source_addr.property.columns[0].type.length
    name = StringField(
        validators=[
            DataRequired("请设置权限名"), Length(1, name_length, message=f"权限名长度不超过{name_length}位")
        ]
    )
    desc = StringField(validators=[Length(0, name_length, message=f"备注名长度不超过{desc_length}位")])
    num = StringField()
    source_addr = StringField(
        validators=[
            DataRequired("请设置权限地址"),
            Length(1, source_addr_length, message=f"权限地址长度不超过{source_addr_length}位")
        ]
    )
    source_type = StringField(validators=[DataRequired("请设置权限类型")])
    source_class = StringField(validators=[DataRequired("请设置权限分类")])

    def validate_name(self, field):
        """ 权限名不重复 """
        self.validate_data_is_not_exist(f"权限名 {field.data} 已存在", Permission, name=field.data)


class FindPermissionForm(BaseForm):
    """ 查找权限参数校验 """
    name = StringField()
    source_addr = StringField()
    source_type = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class DeletePermissionForm(GetPermissionForm):
    """ 删除权限 """

    def validate_id(self, field):
        """ 如果权限在映射表里面被使用了，则不能删除 """
        permission = self.validate_data_is_exist(f"没有id为 {field.data} 的权限", Permission, id=field.data)
        self.validate_data_is_not_exist(f"权限已被角色引用，请先解除引用", RolePermissions, permission_id=field.data)
        setattr(self, "permission", permission)


class EditPermissionForm(GetPermissionForm, CreatePermissionForm):
    """ 编辑权限的校验 """

    def validate_name(self, field):
        """ 校验权限名不重复 """
        self.validate_data_is_not_repeat(
            f"权限名 {field.data} 已存在",
            Permission,
            self.id.data,
            name=field.data
        )

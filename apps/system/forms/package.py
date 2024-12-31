from typing import Optional

from pydantic import Field, field_validator

from ...base_form import BaseForm


class PackageInstallForm(BaseForm):
    name: str = Field(..., title="包名")
    version: Optional[str] = Field(None, title="包版本")

    @field_validator("name")
    def validate_name(cls, value):
        return value.strip()

    @field_validator("version")
    def validate_version(cls, value):
        return value.strip()
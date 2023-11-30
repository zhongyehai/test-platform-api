from ...base_form import BaseForm, required_str_field


class KymProjectForm(BaseForm):
    project: str = required_str_field(title="服务名")


class ChangeKymForm(KymProjectForm):
    kym: dict = required_str_field(title="kym内容")

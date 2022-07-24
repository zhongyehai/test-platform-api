# -*- coding: utf-8 -*-
from utils import restful
from app.assist import assist
from app.assist.models.errorRecord import ErrorRecord
from app.assist.forms.errorRecord import FindErrorForm


@assist.route('/errorRecord/list', methods=['GET'])
# @login_required
def error_record_list():
    """ 错误列表 """
    form = FindErrorForm()
    if form.validate():
        return restful.success(data=ErrorRecord.make_pagination(form))
    return restful.fail(form.get_error())

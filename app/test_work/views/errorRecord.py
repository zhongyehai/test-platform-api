# -*- coding: utf-8 -*-
from app.utils import restful
from app.test_work import test_work
from app.test_work.models.errorRecord import ErrorRecord
from app.test_work.forms.errorRecord import FindErrorForm


@test_work.route('/errorRecord/list', methods=['GET'])
# @login_required
def error_record_list():
    """ 错误列表 """
    form = FindErrorForm()
    if form.validate():
        return restful.success(data=ErrorRecord.make_pagination(form))
    return restful.fail(form.get_error())

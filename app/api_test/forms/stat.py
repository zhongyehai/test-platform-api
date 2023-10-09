# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.baseForm import BaseForm
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.report import ApiReport as Report


class AnalyseForm(BaseForm):
    business_id = IntegerField(validators=[DataRequired("请选择业务线")])
    trigger_type = StringField()
    start_time = StringField()
    end_time = StringField()

    def get_filters(self):
        filters = []
        query_set = Project.query.with_entities(
            Project.id).filter(Project.business_id == self.business_id.data).all()  # [(1,)]
        filters.append(Report.project_id.in_([project_query[0] for project_query in query_set]))

        if self.trigger_type.data:
            filters.append(Report.trigger_type == self.trigger_type.data)
        if self.start_time.data:
            filters.append(Report.created_time.between(self.start_time.data, self.end_time.data))
        return filters

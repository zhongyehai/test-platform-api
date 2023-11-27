# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field

from ...base_form import PaginationForm
from ..model_factory import ApiProject as Project, ApiReport as Report


class AnalyseForm(PaginationForm):
    business_id: int = Field(..., title="业务线id")
    trigger_type: Optional[str] = Field(None, title="触发类型")
    start_time: Optional[str] = Field(None, title="开始时间")
    end_time: Optional[str] = Field(None, title="结束时间")

    def get_query_filter(self):
        filters = []
        query_set = Project.query.with_entities(
            Project.id).filter(Project.business_id == self.business_id).all()  # [(1,)]
        filters.append(Report.project_id.in_([project_query[0] for project_query in query_set]))

        if self.trigger_type:
            filters.append(Report.trigger_type == self.trigger_type)
        if self.start_time:
            filters.append(Report.create_time.between(self.start_time, self.end_time))
        return filters

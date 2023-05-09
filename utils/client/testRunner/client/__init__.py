# -*- coding: utf-8 -*-
class BaseSession:

    def init_step_meta_data(self):
        """ 初始化meta_data，用于存储步骤的执行和结果的详细数据 """
        self.meta_data = {
            "case_id": None,
            "name": "",
            "redirect_print": "",
            "data": [
                {
                    "extract_msgs": {},
                    "request": {
                        "url": "N/A",
                        "method": "N/A",
                        "headers": {}
                    },
                    "response": {
                        "status_code": "N/A",
                        "headers": {},
                        "encoding": None,
                        "content_type": ""
                    }
                }
            ],
            "stat": {
                "content_size": "N/A",
                "response_time_ms": "N/A",
                "elapsed_ms": "N/A",
            }
        }

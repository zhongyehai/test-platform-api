# -*- coding: utf-8 -*-
import io
import os

from jinja2 import Template


def render_html_report(summary):
    """ httprunner原生模板 渲染html报告文件 """
    report_template = os.path.join(os.path.abspath(os.path.dirname(__file__)), r"report_template.html")
    # report_template = os.path.join(os.path.abspath(os.path.dirname(__file__)), r"extent_report_template.html")
    with io.open(report_template, "r", encoding='utf-8') as fp_r:
        template_content = fp_r.read()
        rendered_content = Template(template_content, extensions=["jinja2.ext.loopcontrols"]).render(summary)

        return rendered_content

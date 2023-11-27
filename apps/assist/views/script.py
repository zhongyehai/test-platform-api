# -*- coding: utf-8 -*-
import importlib
import sys
import types
import traceback

from flask import current_app as app

from ..blueprint import assist
from ..model_factory import Script
from ...base_form import ChangeSortForm
from ..forms.script import GetScriptForm, CreatScriptForm, EditScriptForm, DebuggerScriptForm, \
    DeleteScriptForm, GetScriptListForm
from utils.util.file_util import FileUtil
from utils.logs.redirect_print_log import RedirectPrintLogToMemory
from utils.client.test_runner.parser import parse_function, extract_functions


@assist.login_get("/script/list")
def assist_get_script_list():
    """ 自定义脚本文件列表 """
    form = GetScriptListForm()
    if form.detail:
        get_filed = [Script.id, Script.name, Script.script_type, Script.desc, Script.create_user, Script.update_user]
    else:
        get_filed = Script.get_simple_filed_list()
    return app.restful.get_success(Script.make_pagination(form, get_filed=get_filed))


@assist.login_put("/script/sort")
def assist_change_script_sort():
    """ 更新服务的排序 """
    form = ChangeSortForm()
    Script.change_sort(**form.model_dump())
    return app.restful.change_success()


@assist.login_post("/script/copy")
def assist_copy_script():
    """ 复制自定义脚本文件 """
    form = GetScriptForm()
    form.script.copy()
    return app.restful.copy_success()


@assist.login_post("/script/debug")
def assist_debug_script():
    """ 函数调试 """
    form = DebuggerScriptForm()
    name, expression = f'{form.env}_{form.script.name}', form.expression

    # 把自定义函数脚本内容写入到python脚本中
    Script.create_script_file(form.env)

    # 动态导入脚本
    try:
        import_path = f'script_list.{name}'
        func_list = importlib.reload(importlib.import_module(import_path))
        module_functions_dict = {
            name: item for name, item in vars(func_list).items() if isinstance(item, types.FunctionType)
        }
        ext_func = extract_functions(expression)
        func = parse_function(ext_func[0])

        # 重定向print内容到内存
        redirect = RedirectPrintLogToMemory()
        result = module_functions_dict[func["func_name"]](*func["args"], **func["kwargs"])  # 执行脚本
        script_print = redirect.get_text_and_redirect_to_default()

        return app.restful.success(msg="执行成功，请查看执行结果", result={
            "env": form.env,
            "expression": form.expression,
            "result": result,
            "script_print": script_print,
            "script": FileUtil.get_func_data_by_script_name(f'{form.env}_{form.script.name}')
        })
    except Exception as e:
        sys.stdout = sys.__stdout__  # 恢复输出到console
        app.logger.info(str(e))
        error_data = "\n".join("{}".format(traceback.format_exc()).split("↵"))
        return app.restful.fail(msg="语法错误，请检查", result={
            "env": form.env,
            "expression": form.expression,
            "result": error_data,
            "script": FileUtil.get_func_data_by_script_name(f'{form.env}_{form.script.name}')
        })


@assist.login_get("/script")
def assist_get_script():
    """ 获取脚本文件 """
    form = GetScriptForm()
    return app.restful.get_success(form.script.to_dict())


@assist.login_post("/script")
def assist_add_script():
    """ 新增脚本文件 """
    form = CreatScriptForm()
    Script.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/script")
def assist_change_script():
    """ 修改脚本文件 """
    form = EditScriptForm()
    form.script.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_delete("/script")
def assist_delete_script():
    """ 删除脚本文件 """
    form = DeleteScriptForm()
    form.script.delete()
    return app.restful.delete_success()

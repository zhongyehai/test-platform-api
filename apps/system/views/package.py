# -*- coding: utf-8 -*-
import subprocess
from flask import current_app as app

from ..blueprint import system_manage
from ..forms.package import PackageInstallForm
from ...config.model_factory import Config


@system_manage.admin_get("/package/list")
def system_manage_get_package_list():
    """ 获取pip包列表 """
    pip_command = Config.get_pip_command()
    result = subprocess.run([pip_command, 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return app.restful.get_success(result.stdout)


@system_manage.admin_post("/package/install")
def system_manage_install_package():
    """ pip安装包 """
    form = PackageInstallForm()
    package = f'{form.name.strip()}=={form.version.strip()}' if form.version else form.name
    pip_command = Config.get_pip_command()
    result = subprocess.run([pip_command, 'install', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return app.restful.success(msg="安装成功")
    return app.restful.fail(msg=f"安装失败：{result.stderr}")

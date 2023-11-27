# -*- coding: utf-8 -*-
from flask_migrate import Migrate

from apps import create_app, db
from config import _main_server_port

app = create_app()
migrate = Migrate(app, db)


# @app.cli.command()
# def init_data():
#     pass
#     # click.echo('Initializing the roles and permissions and admin...')
#     # Role.init_role()
#     # User.init_user()  # 初始化
#     # click.echo('Done.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=_main_server_port, debug=False)
"""
在 Windows 命令提示符中：set FLASK_APP=main.py
在 Windows PowerShell 中：$env:FLASK_APP="main.py"
在 Linux 或 macOS 的终端中：export FLASK_APP=main.py

flask db init
flask db migrate
flask db upgrade


python -m flask db init
python -m flask db migrate
python -m flask db upgrade
"""

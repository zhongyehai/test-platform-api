# -*- coding: utf-8 -*-
from flask_migrate import Migrate

from apps import create_app, db
from config import _main_server_port

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=_main_server_port, debug=False)

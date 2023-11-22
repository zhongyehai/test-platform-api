# -*- coding: utf-8 -*-
from app import create_app
from config import _main_server_port

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=_main_server_port, debug=False)

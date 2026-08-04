import json
import os

import cherrypy
from QIS import QIS


def json_error_page(status, message, traceback, version):
    # This replaces the default HTML error template
    cherrypy.response.headers["Content-Type"] = "application/json"
    return json.dumps({"status": status, "error": message}).encode("utf-8")


def cors():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
    cherrypy.response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, PUT, DELETE, OPTIONS"
    )
    cherrypy.response.headers["Access-Control-Allow-Headers"] = "*"


cherrypy.tools.cors = cherrypy.Tool("before_handler", cors)

if __name__ == "__main__":
    catalog_address = os.getenv("CATALOG_ADDRESS")
    qis_address = os.getenv("QIS_ADDRESS")
    is_docker = os.getenv("IS_DOCKER") == "true"

    service = QIS(
        catalog_address=catalog_address, qis_address=qis_address, is_docker=is_docker
    )

    service.Start()

    conf = {
        "/": {
            "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
            "tools.staticdir.root": os.path.abspath(os.getcwd()),
            "tools.sessions.on": True,
            "tools.json_out.on": True,
            "tools.json_in.on": True,
            "tools.cors.on": True,
            "request.show_tracebacks": False,
            "request.show_mismatched_params": False,
            "engine.autoreload.on": True,
            "error_page.default": json_error_page,
        },
    }

    cherrypy.config.update(
        {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": 8080,
            "engine.autoreload.on": False,
        }
    )
    cherrypy.tree.mount(service, "/", conf)
    cherrypy.engine.start()
    cherrypy.engine.block()

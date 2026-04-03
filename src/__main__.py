from QIS import QIS
import cherrypy
import os
import json

def json_error_page(status, message, traceback, version):
    # This replaces the default HTML error template
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return json.dumps({
        "status": status,
        "error": message
    }).encode('utf-8')

if __name__ == "__main__":

    catalog_address = os.getenv("CATALOG_ADDRESS")
    qis_address = os.getenv("QIS_ADDRESS")

    service = QIS(catalog_address=catalog_address, qis_address=qis_address)

    service.Start()

    conf={
        '/':{
            'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.sessions.on': True,
            'tools.json_out.on': True,
            'tools.json_in.on': True,
            'request.show_tracebacks': False,
            'request.show_mismatched_params': False,
            'engine.autoreload.on': True,
            'error_page.default': json_error_page
        },
    }
    
    cherrypy.config.update({'server.socket_host': '0.0.0.0', "server.socket_port": 8080, 'engine.autoreload.on': False})
    cherrypy.tree.mount(service, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
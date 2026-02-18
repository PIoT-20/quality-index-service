import cherrypy
import requests as req
import json
import os

class QIS:
    exposed = True

    def __init__(self) -> None:
        self.catalog = os.getenv("CATALOG_ADDRESS")
        if not self.catalog:
            raise ValueError("CATALOG_ADDRESS environment variable not set")
        
        self.address = os.getenv("QIS_ADDRESS")
        if not self.address:
            raise ValueError("QIS_ADDRESS environment variable not set")
        
        try:
            self.register()
        except Exception as e:
            print("Error while registering: ", e)

    
    def register(self) -> None:
        data = {
            "service_type": "QIS",
            "address": self.address,
            "description": "Quality Index Service"
        }

        req.post(f"http://{self.catalog}/service", json=data)

    @cherrypy.expose
    @cherrypy.tools.json_out() # type: ignore
    def GET(self, *uri, **params):
        client_id = params.get("client_id")
        start_time = params.get("start_time")
        end_time = params.get("end_time")

        if not all([client_id, start_time, end_time]):
            raise cherrypy.HTTPError(400, "Missing client_id, start_time or end_time")
        try:
            qis = self.calculate_quality_indexes(client_id, start_time, end_time)
            ret = {
                "client_id": client_id,
                "start_time": start_time,
                "end_time": end_time,
                "quality_indexes": qis
            }
            return ret
        
        except Exception as e:
            raise cherrypy.HTTPError(500, str(e))
        

    def calculate_quality_indexes(self, client_id, start_time, end_time):
        devices = self.get_client_devices(client_id)
        quality_indexes = {}

        for device in devices:
            qi = self.calculate_quality_index(device, start_time, end_time)
            quality_indexes.update(qi)

        return quality_indexes

    def get_client_devices(self, client_id):
        devices = req.get(f"http://{self.catalog}/device?client_id={client_id}").json().get("devices")
        return devices
    
    def get_device_readings(self, device_id, start_time, end_time):
        history_tracking = req.get(f"http://{self.catalog}/service?service=history-tracking").json().get("agent")
        data = req.get(f"http://{history_tracking}/readings?device_id={device_id}&start_time={start_time}&end_time={end_time}").json()
        return data
    
    def get_agent_for_device_type(self, device_type):
        agent = req.get(f"http://{self.catalog}/service?service=agent_{device_type}").json().get("agent")        
        return agent
    
    def get_qi(self, agent, readings):
        qi = req.post(f"http://{agent}/process_readings", json=readings).json().get("quality_index")
        return qi

    def calculate_quality_index(self, device, start_time, end_time):
        try:
            readings = self.get_device_readings(device.get("id"), start_time, end_time)
            agent = self.get_agent_for_device_type(device.get("type"))
            qi = self.get_qi(agent, readings)
            return {device.get("type"): qi}
        except Exception as e:
            print(f'Error calculating quality index for device {device.get("id")}: {e}')
            raise e

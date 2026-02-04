import cherrypy
import requests as req
import json

class QIS:
    exposed = True

    def __init__(self) -> None:
        self.register()
        self.catalog = "http://catalog:8080"

    
    def register(self) -> None:
        """Registers the agent within the IoT platform."""
        pass

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
            return json.dumps(ret)
        
        except Exception as e:
            raise cherrypy.HTTPError(500, str(e))
        

    def calculate_quality_indexes(self, client_id, start_time, end_time):
        devices = self.get_client_devices(client_id)
        quality_indexes = {}

        for device in devices:
            device_id = device.get("id")
            qi = self.calculate_quality_index(device_id, start_time, end_time)
            quality_indexes.update(qi)

        return quality_indexes

    def get_client_devices(self, client_id):
        return [{"id": 1}]
        devices = req.get(f"http://{self.catalog}/devices?client_id={client_id}").json().get("devices")
        return devices
    
    def get_device_readings(self, device_id, start_time, end_time):
        history_tracking = "127.0.0.1:8082"
        #history_tracking = req.get(f"http://{self.catalog}/services?service=history-tracking").json().get("agent")
        data = req.get(f"http://{history_tracking}/readings?device_id={device_id}&start_time={start_time}&end_time={end_time}").json()
        return data
    
    def get_agent_for_device(self, device_id):
        #device_type = req.get(f"http://{self.catalog}/devices?device_id={device_id}").json().get("type")
        #agent = req.get(f"http://{self.catalog}/services?service=agent_{device_type}").json().get("agent")
        
        device_type = "EU-OSHA-noise"
        agent = "127.0.0.1:8083"
        
        return device_type, agent
    
    def get_qi(self, agent, readings):
        qi = req.post(f"http://{agent}/process_readings", json=readings).json().get("quality_index")
        return qi

    def calculate_quality_index(self, device_id, start_time, end_time):
        try:
            readings = self.get_device_readings(device_id, start_time, end_time)
            device_type, agent = self.get_agent_for_device(device_id)
            qi = self.get_qi(agent, readings)
            return {device_type: qi}
        except Exception as e:
            print(f"Error calculating quality index for device {device_id}: {e}")
            return {}

        #return {device_type: qi}

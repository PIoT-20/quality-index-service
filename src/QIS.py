import cherrypy
import requests as req
import json
import os

class QIS:
    exposed = True

    def __init__(self, catalog_address, qis_address) -> None:
        self.catalog = catalog_address
        if not self.catalog:
            raise ValueError("CATALOG_ADDRESS must be provided")
        
        self.address = qis_address
        if not self.address:
            raise ValueError("QIS_ADDRESS must be provided")
        
        self.load_cfg()
        
    def load_cfg(self):
        try:
            self.cfg = json.load(open("cfg.json", "r"))
        except FileNotFoundError:
            self.cfg = {}

    def save_cfg(self):
        json.dump(self.cfg, open("cfg.json", "w"))

    
    def Start(self):
        if not self.cfg.get("service_id"):
            self.register()
        else:
            self.update_registration()

    def register(self) -> None:
        data = {
            "service_type": "QIS",
            "address": self.address,
            "description": "Quality Index Service"
        }

        response = req.post(f"{self.catalog}/service", json=data)
        if response.status_code == 201:
            self.cfg["service_id"] = response.json().get("_id").get("$oid")
            self.save_cfg()
        else:
            raise Exception(f"Failed to register service: {response.text}")


    def update_registration(self) -> None:
        data = {
            "id": {"$oid": self.cfg["service_id"]},
            "service_type": "QIS",
            "address": self.address,
            "description": "Quality Index Service"
        }

        response = req.put(f"{self.catalog}/service/", json=data)
        if response.status_code == 201:
            print("Registration updated successfully. Id: ", self.cfg["service_id"])
        else:
            raise Exception(f"Failed to update registration: {response.text}")
        

    @cherrypy.expose
    @cherrypy.tools.json_out() # type: ignore
    def GET(self, *uri, **params):
        user_id = params.get("user_id")
        start_time = params.get("start_time")
        end_time = params.get("end_time")

        if not all([user_id, start_time, end_time]):
            raise cherrypy.HTTPError(400, "Missing user_id, start_time or end_time")
        try:
            qis = self.calculate_quality_indexes(user_id, start_time, end_time)
            ret = {
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time,
                "quality_indexes": qis
            }
            return ret
        
        except Exception as e:
            print(f"Error calculating quality indexes for user {user_id}: {e}")
            raise cherrypy.HTTPError(500, "Internal Server Error: ")
        

    def calculate_quality_indexes(self, user_id, start_time, end_time):
        devices = self.get_client_devices(user_id)
        quality_indexes = []

        for device in devices:
            try:
                qi = self.calculate_quality_index(device, start_time, end_time)
                quality_indexes.append({
                    "device_id": device.get("_id").get("$oid"),
                    "device_type": device.get("device_type"),
                    "location": device.get("location"),
                    "quality_index": qi
                })
            except Exception as e:
                print(f'Error calculating quality index for device {device.get("_id").get("$oid")}: {e}')
                
        return quality_indexes

    def get_client_devices(self, user_id):
        response = req.get(f"{self.catalog}/device?user_id={user_id}")
        if response.status_code != 200:
            raise Exception(f"Failed to get devices for user {user_id}: {response.text}")
        devices = response.json()
        return devices
    
    def get_history_tracking_address(self):
        response = req.get(f"{self.catalog}/service?service_type=history-tracking")
        if response.status_code == 404:
            raise Exception("No history tracking service found in catalog")
        if response.status_code != 200:
            raise Exception(f"Failed to get history tracking service: {response.text}")
        return response.json().get("address")

    def get_device_readings(self, device_id, start_time, end_time):
        history_tracking = self.get_history_tracking_address()

        response = req.get(f"{history_tracking}/readings?device_id={device_id}&start_time={start_time}&end_time={end_time}")
        if response.status_code == 404:
            raise Exception(f"No readings found for device {device_id} in history tracking")
        if response.status_code != 200:
            raise Exception(f"Failed to get readings for device {device_id} from history tracking: {response.text}")
        return response.json().get("readings", [])
    
    def get_agent_for_device_type(self, device_type):
        response = req.get(f"{self.catalog}/service?service_type=agent_{device_type}")
        if response.status_code == 404:
            raise Exception(f"No agent found for device type {device_type}")
        elif response.status_code != 200:
            raise Exception(f"Failed to get agent for device type {device_type}: {response.text}") 
        return response.json().get("address")   
    
    def get_qi(self, agent, readings):
        response = req.post(f"{agent}/process_readings", json={"readings": readings})
        qi = response.json().get("quality_index")
        return qi

    def calculate_quality_index(self, device, start_time, end_time):
        readings = self.get_device_readings(device.get("_id").get("$oid"), start_time, end_time)
        if len(readings) == 0:
            raise Exception(f"No readings found for device {device.get('_id').get('$oid')} between {start_time} and {end_time}")
        agent = self.get_agent_for_device_type(device.get("device_type"))
        qi = self.get_qi(agent, readings)
        return qi

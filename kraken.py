import json
import requests
from task_in_progress import TaskInProgress
from spaceknow_tools import DetectionTile


URL = "https://spaceknow-kraken.appspot.com"

class Kraken(TaskInProgress):
    def __init__(self, sceneId, extent, map_type, headers={"content-type": "application/json"}):
        self.sceneId = sceneId
        self.extent = extent
        assert map_type in ["imagery", "aircraft", "ships", "wrunc", "cars", "containers", "boats",
                            "solar-panels", "pools", "houses", "coal", "cranes", "lithium", "cows",
                            "change", "s2-change", "sar-change", "wrunc-change", "eme", "trees", "ndvi"]
        self.map_type = map_type
        self.features = []
        self.headers = headers

    def initiate(self):
        payload = {
            "sceneId": self.sceneId,
            "extent": self.extent
        }
        response = requests.post(
            URL + "/kraken/release/" + self.map_type + "/geojson/initiate",
            headers=self.headers,
            data=json.dumps(payload))
        if response.status_code == 200:
            response_json = response.json()
            self.pipelineId = response_json["pipelineId"]
            self.status = response_json["status"]
        else:
            print(response.status_code)
            print(response.json())
            self.status = "FAILED"

    def retrieve(self):
        "/kraken/release/{map_type}/geojson/retrieve"
        payload = {
            "pipelineId": self.pipelineId
        }
        response = requests.post(
            URL + "/kraken/release/" + self.map_type + "/geojson/retrieve",
            headers=self.headers,
            data=json.dumps(payload))
        if response.status_code == 200:
            response_json = response.json()
            response_json
            maiId = response_json["mapId"]
            tiles = response_json["tiles"]
            for tile in tiles:
                dt = DetectionTile(maiId, tile)
                self.features.extend(dt.features)
        else:
            print(response.status_code)
            print(response.json())

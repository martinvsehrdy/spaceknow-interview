import json
import requests
import wget
import os
from io import BytesIO
import tarfile
import struct
import numpy as np
import cv2
from urllib.request import urlopen
from task_in_progress import TaskInProgress
from spaceknow_tools import SatelliteImagery, Metadata, Band

URL = "https://spaceknow-imagery.appspot.com"


class SearchScene(TaskInProgress):
    def __init__(self, satelite_imagery, extent, startDatetime=None, endDatetime=None, minIntersection=None, headers={"content-type": "application/json"}):
        '''
        Args:
            satelite_imagery(SatelliteImagery): contains provider and dataset for scene request
            extent (object): area to be searched. See Extent.
            startDatetime (string): UTC date-time filter in format YYYY-MM-DD HH:MM:SS
            endDatetime (string): UTC date-time filter in format YYYY-MM-DD HH:MM:SS
            minIntersection (float): a number between 0 and 1 (0≤i≤1). 0 means arbitrarily but still present intersection.
        '''
        self.satelite_imagery = satelite_imagery
        self.extent = extent
        self.startDatetime = startDatetime
        self.endDatetime = endDatetime
        self.minIntersection = minIntersection
        self.headers = headers
        self.results = []
        self.pipelineId = None
        self.status = None

    def initiate(self):
        payload = {
            "provider": self.satelite_imagery.provider,
            "dataset": self.satelite_imagery.dataset,
            "extent": self.extent
        }
        if self.startDatetime is not None:
            payload["startDatetime"] = self.startDatetime
        if self.endDatetime is not None:
            payload["endDatetime"] = self.endDatetime
        if self.minIntersection is not None:
            payload["minIntersection"] = self.minIntersection

        response = requests.post(
            URL + "/imagery/search/initiate",
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
        return self.status, self.pipelineId

    def retrieve(self):
        payload = {
            "pipelineId": self.pipelineId
        }
        response = requests.post(
            URL + "/imagery/search/retrieve",
            headers=self.headers,
            data=json.dumps(payload))
        if response.status_code == 200:
            response_json = response.json()
            self.results = [Metadata.fromDictData(result) for result in response_json["results"]]
        else:
            print(response.status_code)
            print(response.json())

class SKImage:
    data_type_dict = {
        8: np.uint8,
        9: np.int8,
        16: np.uint16,
        17: np.int16,
        32: np.uint32,
        33: np.int32,
        64: np.uint64,
        65: np.int64,
    }
    def __init__(self, fileobj):
        '''
        Driver to use *.ski file (actually *.tar.gz) that include info.json, meta.json and 0000x.skb
        Args:
            ski_file (tarfile): handler to opened file, handler has methods read()

        '''
        tfile = tarfile.open(fileobj=fileobj)
        ski_info = tfile.extractfile("info.json").read()
        ski_info = json.loads(ski_info)
        ski_meta = tfile.extractfile("meta.json").read()
        ski_meta = json.loads(ski_meta)
        self.metadata = ski_meta

        img_channels = {}
        for index, band in enumerate(ski_info["bands"]):
            skband_file = tfile.extractfile(str(index).zfill(5) + ".skb")

            img = self.parse_skband_file(skband_file)
            img_channels.setdefault(band["names"][0], img)
            #if band["names"][0].find("MASK") >= 0:
            #    cv2.imshow(band["names"][0], 100*img.astype(np.uint8))
            #else:
            #    cv2.imshow(band["names"][0], img.astype(np.uint8))
            #cv2.waitKey(1)

        self.imageRGB = np.stack((img_channels["blue"], img_channels["green"], img_channels["red"]), axis=2)
        self.imageRGB = self.imageRGB.astype(np.uint8)

    def parse_skband_file(self, skband_file):
        data_type_idx = struct.unpack("<H", skband_file.read(2))[0]
        data_type = self.data_type_dict.get(data_type_idx)
        num_columns = struct.unpack("<I", skband_file.read(4))[0]
        num_rows = struct.unpack("<I", skband_file.read(4))[0]
        bitdepth = data_type_idx & ~0x01
        ret = np.zeros((num_rows, num_columns), dtype=data_type)
        num_bytes_in_row = num_columns * bitdepth//8
        for r in range(num_rows):
            row_bytes = skband_file.read(num_bytes_in_row)
            next_row = np.frombuffer(row_bytes, dtype=data_type)
            if r == 0:
                ret[r,:] = next_row
            else:
                ret[r,:] = ret[r-1,:] + next_row

        return ret

class GetImage(TaskInProgress):
    def __init__(self, sceneId, extent, resolution=None, headers={"content-type": "application/json"}):
        '''
        Args:
            sceneId (string):
            extent (object):
            resolution (float):
        '''
        self.sceneId = sceneId
        self.extent = extent
        self.resolution = resolution
        self.headers = headers
        self.pipelineId = None
        self.status = None

    def initiate(self):
        payload = {
            "sceneId": self.sceneId,
            "extent": self.extent
        }
        if self.resolution is not None:
            payload.setdefault("resolution", self.resolution)

        response = requests.post(
            URL + "/imagery/get-image/initiate",
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
        payload = {
            "pipelineId": self.pipelineId
        }
        response = requests.post(
            URL + "/imagery/get-image/retrieve",
            headers=self.headers,
            data=json.dumps(payload))
        if response.status_code == 200:
            response_json = response.json()
            self.meta = response_json["meta"]
            self.extent = response_json["extent"]
            url = response_json["url"]
            urlstream = urlopen(url)
            tempfile = BytesIO()
            tempfile.write(urlstream.read())
            tempfile.seek(0)
            self.skimage = SKImage(tempfile)
        else:
            print(response.status_code)
            print(response.json())

    def save_ski(self, url):
        pass

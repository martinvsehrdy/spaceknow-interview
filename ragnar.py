import json
import requests
from task_in_progress import TaskInProgress

URL = "https://spaceknow-imagery.appspot.com"

# preview-multispectral
# preview-swir
# preview-panchromatic
class SatelliteImagery:
    def __init__(self, provider, dataset):
        '''
        contains provider and its dataset
        Args:
            provider (string):
            dataset (string):
        '''
        assert provider in ["gbdx", "pl", "ab", "ee"]
        self.provider = provider
        if provider == "gbdx":
            assert dataset in ["preview-multispectral", "idaho-pansharpened", "preview-swir", "idaho-swir", "preview-panchromatic", "idaho-panchromatic"]
        if provider == "pl":
            assert dataset in ["PSOrthoTile"]
        if provider == "ab":
            assert dataset in ["spot", "pleiades"]
        if provider == "ee":
            assert dataset in ["COPERNICUS/S1_GRD", "COPERNICUS/S2", "LANDSAT/LC08/C01/T1", "LANDSAT/LE07/C01/T1", "MODIS/006/MOD08_M3", "MODIS/006/MYD08_M3"]
        self.dataset = dataset

    def __repr__(self):
        return f"{self.provider}:{self.dataset}"

class Band:
    def __init__(self, names, bitDepth, gsd, pixelSizeX, pixelSizeY, crsOriginX, crsOriginY,
                 approximateResolutionX, approximateResolutionY,
                 radianceMult=1, radianceAdd=0, reflectanceMult=1, reflectanceAdd=0):
        self.names = names
        self.bitDepth = bitDepth
        self.gsd = gsd
        self.pixelSizeX = pixelSizeX
        self.pixelSizeY = pixelSizeY
        self.crsOriginX = crsOriginX
        self.crsOriginY = crsOriginY
        self.approximateResolutionX = approximateResolutionX
        self.approximateResolutionY = approximateResolutionY
        self.radianceMult = radianceMult
        self.radianceAdd = radianceAdd
        self.reflectanceMult = reflectanceMult
        self.reflectanceAdd = reflectanceAdd

    def __repr__(self):
        return f"{self.names[0]} pixelSize={self.pixelSizeX}x{self.pixelSizeY}"

    @classmethod
    def fromDictData(cls, data):
        optional_arguments = {}
        if data.get("radianceMult") is not None:
            optional_arguments["radianceMult"] = data["radianceMult"]
        if data.get("radianceAdd") is not None:
            optional_arguments["radianceAdd"] = data["radianceAdd"]
        if data.get("reflectanceMult") is not None:
            optional_arguments["reflectanceMult"] = data["reflectanceMult"]
        if data.get("reflectanceAdd") is not None:
            optional_arguments["reflectanceAdd"] = data["reflectanceAdd"]
        return  cls(names=data["names"],
                   bitDepth = data["bitDepth"],
                   gsd = data["gsd"],
                   pixelSizeX = data["pixelSizeX"],
                   pixelSizeY = data["pixelSizeY"],
                   crsOriginX = data["crsOriginX"],
                   crsOriginY = data["crsOriginY"],
                   approximateResolutionX = data["approximateResolutionX"],
                   approximateResolutionY = data["approximateResolutionY"],
                   **optional_arguments)

class Metadata:
    def __init__(self, sceneId, satellite_imagery, satellite, datetime, crsEpsg, footprint,
                 offNadir=None, sunElevation=None, sunAzimuth=None, satelliteAzimuth=None,
                 cloudCover=None, anomalousRatio=None, bands=[]):
        '''
        Args:
            sceneId (string):
            satellite_imagery (SatelliteImagery):
            satellite:
            datetime:
            crsEpsg:
            footprint:
            offNadir:
            sunElevation:
            sunAzimuth:
            satelliteAzimuth:
            cloudCover:
            anomalousRatio:
            bands:
        '''
        self.sceneId = sceneId
        self.satellite_imagery = satellite_imagery
        self.satellite = satellite
        self.datetime = datetime
        self.crsEpsg = crsEpsg
        self.footprint = footprint
        self.offNadir = offNadir
        self.sunElevation = sunElevation
        self.sunAzimuth = sunAzimuth
        self.satelliteAzimuth = satelliteAzimuth
        self.cloudCover = cloudCover
        self.anomalousRatio = anomalousRatio
        self.bands = bands

    def __repr__(self):
        return f"sceneId={self.sceneId} {self.satellite_imagery}, {self.datetime}, bands={len(self.bands)}"

    @classmethod
    def fromDictData(cls, data):
        optional_arguments = {}
        if data.get("offNadir") is not None:
            optional_arguments["offNadir"] = data["offNadir"]
        if data.get("sunElevation") is not None:
            optional_arguments["sunElevation"] = data["sunElevation"]
        if data.get("sunAzimuth") is not None:
            optional_arguments["sunAzimuth"] = data["sunAzimuth"]
        if data.get("satelliteAzimuth") is not None:
            optional_arguments["satelliteAzimuth"] = data["satelliteAzimuth"]
        if data.get("cloudCover") is not None:
            optional_arguments["cloudCover"] = data["cloudCover"]
        if data.get("anomalousRatio") is not None:
            optional_arguments["anomalousRatio"] = data["anomalousRatio"]
        return cls(sceneId=data["sceneId"],
                   satellite_imagery=SatelliteImagery(data["provider"], data["dataset"]),
                   satellite=data["satellite"],
                   datetime=data["datetime"],
                   crsEpsg=data["crsEpsg"],
                   footprint=data["footprint"],
                   bands=[Band.fromDictData(d) for d in data["bands"]],
                   **optional_arguments)



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
    def __init__(self, ski_file):
        self.ski_file = ski_file

class GetImage:
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
            "extent": self.extent,
            "resolution": self.resolution
        }
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
        pass

    def save_ski(self, url):
        pass

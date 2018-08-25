import json
import requests

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

    @classmethod
    def fromDictData(cls, data):
        cls(names=data["names"],
            bitDepth=data["bitDepth"],
            gsd=data["gsd"],
            pixelSizeX=data["pixelSizeX"],
            pixelSizeY=data["pixelSizeY"],
            crsOriginX=data["crsOriginX"],
            crsOriginY=data["crsOriginY"],
            approximateResolutionX=data["approximateResolutionX"],
            approximateResolutionY=data["approximateResolutionY"],
            radianceMult=data["radianceMult"],
            radianceAdd=data["radianceAdd"],
            reflectanceMult=data["reflectanceMult"],
            reflectanceAdd=data["reflectanceAdd"])

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
        self.sceneId =sceneId
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

    @classmethod
    def fromDictData(cls, data):
        cls(sceneId=data["sceneId"],
            satellite_imagery=SatelliteImagery(data["provider"], data["dataset"]),
            satellite=data["satellite"],
            datetime=data["datetime"],
            crsEpsg=data["crsEpsg"],
            footprint=data["footprint"],
            offNadir=data["offNadir"],
            sunElevation=data["sunElevation"],
            sunAzimuth=data["sunAzimuth"],
            satelliteAzimuth=data["satelliteAzimuth"],
            cloudCover=data["cloudCover"],
            anomalousRatio=data["anomalousRatio"],
            bands=[Band.fromDictData(d) for d in data["bands"]])


class SearchScene:
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
        self.metadata = None
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
            self.metadata = Metadata.fromDictData(response_json)
        else:
            print(response.status_code)
            print(response.json())


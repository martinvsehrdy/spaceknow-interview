import geojson
import numpy as np
import cv2
from pyreproj import Reprojector
from urllib.request import urlopen

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

class DetectionTile:
    def __init__(self, mapId, tile, geometryId="-"):
        self.mapId = mapId
        self.geometry_id = geometryId
        self.zoom, self.x, self.y = tile
        self.features = []
        f = urlopen(self.url())
        g = geojson.loads(f.read())
        self.features = g.features

    def url(self):
        return f"https://spaceknow-kraken.appspot.com/kraken/grid/{self.mapId}/{self.geometry_id}/{self.zoom}/{self.x}/{self.y}/detections.geojson"

class EPSGTransformator:
    def __init__(self, crsEpsg):
        self.crsEpsg = crsEpsg
        rp = Reprojector()
        self.transform_fce = rp.get_transformation_function(to_srs=crsEpsg)

    def transform(self, points):
        '''
        Transform points coordinates from WGS84 to coordinates defined as crsEpsg
        Args:
            points (list of list of float): list of Points, where Point is list of float

        Returns: list of Points in new coordinates
        '''
        return [self.transform_fce(p[0], p[1]) for p in points]

def draw_extent(image, crsOrigin, pixelSize, polygons, color):
    '''
    Draw extent (polygon) to image.
    Args:
        image (np.array):
        crsOrigin (list of crsOrigin): [crsOriginX, crsOriginY] from metadata
        pixelSize(list of pixelSize): [pixelSizeX, pixelSizeY] from metadata
        polygons (list of list of list of float): list of Polygons, Polygon is list of Points, Point is list of floats
        color (tuple of int): tuple of 3 numbers representing RGB - red green, blue
    Returns: image
    '''
    npcrsOriginXY = np.array(crsOrigin)
    nppixelSizeXY = np.array(pixelSize)
    for polygon in polygons:
        dif = np.array(polygon) - npcrsOriginXY
        polygon_to_draw = np.divide(dif, nppixelSizeXY).astype(np.int)
        cv2.polylines(image, [polygon_to_draw], True, color, thickness=3)

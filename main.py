import os
import time
import json
import geojson
from authorization import SpaceKnowTestAuth, SpaceKnowAuth
from ragnar import SearchScene, SatelliteImagery

token_file = "token_file.json"
auth = SpaceKnowAuth(username="a6427229@nwytg.net", password="AW3EDCc", token_file=token_file)
works_in_progress = []

geojsons_dir = "geojsons"

for geojson_file in os.listdir(geojsons_dir):
    geojson_file = os.path.join(geojsons_dir, geojson_file)
    extent = geojson.load(open(geojson_file))
    satelit = SatelliteImagery("gbdx", "preview-multispectral")
    search = SearchScene(satelit, extent, headers=auth.headers())
    status, pipelineId = search.initiate()
    print(status, pipelineId)
    if search.status == "NEW":
        works_in_progress.append(search)

for work in works_in_progress:
    work


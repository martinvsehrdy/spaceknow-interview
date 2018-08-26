import os
import time
import json
import geojson
from authorization import SpaceKnowTestAuth, SpaceKnowAuth
from ragnar import SearchScene, SatelliteImagery

token_file = "token_file.json"
auth = SpaceKnowAuth(username="a6427229@nwytg.net", password="AW3EDCc", token_file=token_file)
works_in_progress = []

geojsons_dir = "Extent"

geojson_list = os.listdir(geojsons_dir)
for geojson_file in geojson_list:
    geojson_file = os.path.join(geojsons_dir, geojson_file)
    extent = geojson.load(open(geojson_file))
    satelit = SatelliteImagery("gbdx", "idaho-pansharpened")
    search = SearchScene(satelit, extent, headers=auth.headers())
    status, pipelineId = search.initiate()
    print(status, pipelineId)
    if search.status == "NEW":
        works_in_progress.append(search)
    time.sleep(1.0)
    search.retrieve()
    search.results


for work in works_in_progress:
    work.checkStatus()
    if work.status == "RESOLVED":
        work.retrieve()


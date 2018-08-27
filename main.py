import os
import time
import json
import argparse
import geojson
import re
import numpy as np
import cv2
from authorization import SpaceKnowTestAuth, SpaceKnowAuth
from ragnar import SearchScene, SatelliteImagery, GetImage
from kraken import Kraken


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--username", help="username of Spaceknow account", required=False)
    ap.add_argument("-p", "--password", help="password of Spaceknow account", required=False)
    ap.add_argument("-t", "--token-file", help="file where to save/load token for future usage", required=False, default=None)
    ap.add_argument("-g", "--geojson", help="GeoJSON file that contains single Geometry", required=True)
    args = vars(ap.parse_args())

    geojson_file = args["geojson"]
    token_file = args.get("token_file")
    username = args.get("username", "")
    password = args.get("password", "")
    # auth = SpaceKnowAuth(username="a6427229@nwytg.net", password="AW3EDCc", token_file="token_file.json")
    auth = SpaceKnowAuth(username=args.get("username"), password=args.get("password"), token_file=token_file)

    extent = geojson.load(open(geojson_file))
    satelit = SatelliteImagery("gbdx", "idaho-pansharpened")
    search = SearchScene(satelit, extent, headers=auth.headers())
    status, pipelineId = search.initiate()
    search.wait_till_job_is_done()

    # Searching Scene is done
    if search.status == "RESOLVED":
        search.retrieve()
        for metadata in search.results:
            # download .ski file and extract image
            getimage = GetImage(sceneId=metadata.sceneId, extent=extent, headers=auth.headers())
            getimage.initiate()
            getimage.wait_till_job_is_done()
            if getimage.status == "RESOLVED":
                getimage.retrieve()
                rgb_image = getimage.skimage.imageRGB

            # get detections and draw cars to image
            features = []
            kraken = Kraken(metadata.sceneId, extent, "cars", auth.headers())
            kraken.initiate()
            kraken.wait_till_job_is_done()
            if kraken.status == "RESOLVED":
                kraken.retrieve()
                features.extend(kraken.features)
            # print result depends on shoot time
            img_file = metadata.datetime + "_" + metadata.satellite + ".png"
            img_file = re.sub('[^-a-zA-Z0-9_.() ]+', '_', img_file)
            print(metadata.datetime, metadata.satellite)
            cv2.imwrite(img_file, rgb_image)
            print(f"Image saved to {img_file}")
            print(f"Number of cars is {len(features)}")

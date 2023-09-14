import ee
import datetime
import geopandas as gpd
import importlib
import rasterio
import gdal
import requests
import zipfile
import numpy as np
from Tasks import TCF_mapping as tasks
from PIL import Image

ee.Initialize()

def main():
	tasks.maploop()
if __name__ == '__main__':
  main()

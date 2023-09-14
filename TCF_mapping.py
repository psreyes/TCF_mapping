import ee
import json
import datetime
import json
import geojson
import pandas as pd
import geopandas as gpd
import rasterio
import gdal
import importlib
import sys
import requests
import zipfile
import config_variables as config
import os
from os import listdir
from os.path import isfile,join
import numpy as np
from PIL import Image
import netCDF4
from netCDF4 import Dataset
from Models import model_GPP

ee.Initialize()
ee.Authenticate()

#Config variables

import datetime

ee.Initialize()

config.S3Olci = ee.ImageCollection("COPERNICUS/S3/OLCI")

config.S3TOAGPR = ee.ImageCollection("users/pablosrmz/GPP/FVT_2019")

config.TROPOSIF = ee.ImageCollection("users/pablosrmz/GPP/TROPOSIF_World_2019")

config.fc = ee.FeatureCollection("users/pablosrmz/ne_10m_land")

config.fechaInicioSecuencia = ee.Date('2019-01-01')

config.iteracionesDias = round(ee.Date('2020-01-01').difference(fechaInicioSecuencia, 'day').getInfo()/8)

config.assetPath='users/pablosrmz/GPP/GPP_2019/'

config.region=fc.geometry()

fileName='GPP_'

variables_GREEN = {'GPP':['GPP', 100, 0]}

bands = ['GREEN', 'UNCERTAINTY_GREEN', 'QUALITY_FLAG']

#Ancilliary functions

def sequence_GREEN(variable):
	sequence_GREEN = []
	model = globals()['model_' + variable]
	for i in range(0, model.XTrain_dim_GREEN):
		sequence_GREEN.append(str(i))
	return sequence_GREEN

def getInputDates(i):
	fecha_inicio = config.fechaInicioSecuencia.advance(ee.Number(i*8), 'day')
	fecha_inicio_h = config.fechaInicioSecuencia_h.advance(ee.Number(i*8), 'hour')
	fecha_fin = fecha_inicio.advance(8, 'day')
	fecha_fin_h = fecha_inicio_h.advance(8, 'hour')
	fecha_str = datetime.datetime.utcfromtimestamp(fecha_inicio.getInfo()['value']/1000.0).strftime('%Y%m%d')
	return {'fecha_inicio':fecha_inicio, 'fecha_fin':fecha_fin, 'fecha_str':fecha_str, 'fecha_inicio_h':fecha_inicio_h, 'fecha_fin_h':fecha_fin_h}

def addTimePropS3TOA(image):

	 image_timed_S3TOA = image.set('system:time_start', ee.Date(image.getString('system:index').slice(-8,-4).cat('-').cat(image.getString('system:index').slice(-4,-2)).cat('-').cat(image.getString('system:index').slice(-2))))

	return image_timed_S3TOA

def addTimePropTROPOSIF(image):

	image_timed_TROPOSIF = image.set('system:time_start', ee.Date(image.getString('system:index').slice(-10)))

	return image_timed_TROPOSIF

def maskS3badPixels(image):

  qa = ee.Image(image.select('quality_flags'));
  coastLine = 1 << 30;
  inLandWater = 1 << 29;
  bright = 1 << 27;
  invalid = 1 << 25;
  Oa12Sat = 1 << 9;
  mask = qa.bitwiseAnd(coastLine).eq(0).And(qa.bitwiseAnd(inLandWater).eq(0)).And(qa.bitwiseAnd(bright).eq(0))

  return image.updateMask(mask);

def addVariables(image):

  date = ee.Date(image.get("system:time_start"));
  years = date.difference(ee.Date('1970-01-01'),'days');
  return image.addBands(ee.Image(years).rename('t').float());

def compose_image(fecha_inicio, fecha_fin, fecha_inicio_str, n, S3TOAGPR, SIFColl):

  LCC = ee.Image(S3TOAGPR
  .filterDate(fecha_inicio, fecha_fin)
  .select('LCC_GREEN')
  .median()).divide(10000)

  LAI = ee.Image(S3TOAGPR
  .filterDate(fecha_inicio, fecha_fin)
  .select('LAI_GREEN')
  .median()).divide(10000)

  FAPAR = ee.Image(S3TOAGPR
  .filterDate(fecha_inicio, fecha_fin)
  .select('FAPAR_GREEN')
  .median()).divide(10000)

  FVC = ee.Image(S3TOAGPR
  .filterDate(fecha_inicio, fecha_fin)
  .select('FVC_GREEN')
  .median()).divide(10000)

  ERA = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")

  CFSR = ee.ImageCollection("NOAA/CFSR")

  TMean = ERA.filterDate(getInputDates(n)['fecha_inicio_h'], getInputDates(n)['fecha_fin_h']).select('temperature_2m').mean().multiply(1.8)

  TMeanC = ERA.filterDate(getInputDates(n)['fecha_inicio_h'], getInputDates(n)['fecha_fin_h']).select('temperature_2m').mean().subtract(273.3)

  PAR = ERA.filterDate(getInputDates(n)['fecha_inicio'], getInputDates(n)['fecha_fin']).select('surface_solar_radiation_downwards_hourly').mean().divide(3600)

  TMean = ERA.filterDate(getInputDates(n)['fecha_inicio'], getInputDates(n)['fecha_fin']).select('temperature_2m').mean().multiply(1.8).multiply(0.7)

  TMeanC = ERA.filterDate(getInputDates(n)['fecha_inicio'], getInputDates(n)['fecha_fin']).select('temperature_2m').mean().subtract(273.3).multiply(0.7)

  h = CFSR.select('Relative_humidity_entire_atmosphere_single_layer').filterDate(getInputDates(0)['fecha_inicio'].advance(1, 'year'), getInputDates(0)['fecha_fin'].advance(1, 'year')).mean()

  vpsat = ((ee.Image(-10440.379).divide(TMean)).add(-11.29465).add(TMean.multiply(-0.027022355)).add(TMean.multiply(TMean).multiply(0.00001289036)).add(TMean.multiply(TMean).multiply(TMean).multiply(-0.0000000024780681)).add((TMean.log()).multiply(6.5459673))).exp()

  vpair = (vpsat.multiply(h.divide(100)))

  VPD = vpsat.subtract(vpair).multiply(6894.76)

  SIF743 = SIFColl.filterDate(fecha_inicio, fecha_fin).mean()

  SIF743_resc = SIF743.resample('bilinear').reproject(crs=SIF743.select('b1').projection().crs(), scale=300)

  return ee.Image(PAR.addBands(TMeanC).addBands(vpair.multiply(68.947)).addBands(LCC).addBands(LAI).addBands(FAPAR).addBands(FVC).addBands(SIF743_resc))


def calculate_GREEN(fecha_inicio, fecha_fin, fecha_inicio_str, variable, limitUp, limitDown, n, S3TOAGPR, SIFColl):


  model = globals()['model_' + variable]

  image = compose_image(fecha_inicio, fecha_fin, fecha_inicio_str, n, S3TOAGPR, SIFColl).clipToCollection(config.fc);

  im_norm_ell2D_hypell = image.subtract(model.mx_GREEN).divide(model.sx_GREEN).multiply(model.hyp_ell_GREEN).toArray().toArray(1);
  im_norm_ell2D = image.subtract(model.mx_GREEN).divide(model.sx_GREEN).toArray().toArray(1);
  PtTPt  = im_norm_ell2D_hypell.matrixTranspose().matrixMultiply(im_norm_ell2D).arrayProject([0]).multiply(-0.5); #OK

  PtTDX  = ee.Image(model.X_train_GREEN).matrixMultiply(im_norm_ell2D_hypell).arrayProject([0]).arrayFlatten([sequence_GREEN(variable)]);
  arg1   = PtTPt.exp().multiply(model.hyp_sig0_GREEN);
  k_star = PtTDX.subtract(model.XDX_pre_calc_GREEN.multiply(0.5)).exp().toArray();
  mean_pred = k_star.arrayDotProduct(model.alpha_coefficients_GREEN.toArray()).multiply(arg1);
  mean_pred = mean_pred.toArray(1).arrayProject([0]).arrayFlatten([[variable + '_GREEN']]);
  mean_pred = mean_pred.add(model.mean_model_GREEN);#.updateMask(mean_pred.gt(0));
  filterDown = mean_pred.gt(limitDown)

  filterUp = mean_pred.lt(limitUp)

  quality_flags = (filterDown.multiply(filterUp)).Not().toArray().arrayFlatten([[variable + '_QUALITY_FLAG']])

  k_star_uncert = PtTDX.subtract(model.XDX_pre_calc_GREEN.multiply(0.5)).exp().multiply(arg1).toArray();
  Vvector = ee.Image(model.LMatrixInverse).matrixMultiply(k_star_uncert.toArray(0).toArray(1)).arrayProject([0])
  Variance = ee.Image(model.hyp_sig_GREEN).toArray().subtract(Vvector.arrayDotProduct(Vvector)).sqrt()
  Variance = Variance.toArray(1).arrayProject([0]).arrayFlatten([[variable + '_UNCERTAINTY_GREEN']])


  image= image.addBands(mean_pred);
  image = image.addBands(Variance);
  image = image.addBands(quality_flags);

  return image.select(variable + '_GREEN', variable + '_UNCERTAINTY_GREEN', variable + '_QUALITY_FLAG');

def maploop():

	S3TOAGPR = config.S3TOAGPR.map(addTimePropS3TOA)

	SIFColl = config.TROPOSIF.map(addTimePropTROPOSIF)

	for i in range(0,config.iteracionesDias):

		imageHolder = ee.Image();

		for variable_GREEN in config.variables_GREEN:
			params = config.variables_GREEN[variable_GREEN]
			variable = params[0]
			limitUp = params[1]
			limitDown = params[2]
			imagen = calculate_GREEN(getInputDates(i)['fecha_inicio'], getInputDates(i)['fecha_fin'], getInputDates(i)['fecha_str'], variable, limitUp, limitDown, i, S3TOAGPR, SIFColl)
			imageHolder = imageHolder.addBands(imagen)

		image_export = imageHolder.select('GPP_GREEN', 'GPP_UNCERTAINTY_GREEN')

		exportar = ee.batch.Export.image.toAsset(
		assetId=config.assetPath + config.fileName + getInputDates(i)['fecha_str'],
		image=image_export,
		maxPixels=1e10,
		crs='EPSG:3857',
		description=config.fileName + getInputDates(i)['fecha_str'],
		scale=300,
		region=config.region#.bounds().getInfo()['coordinates']
		)
		exportar.start()
		exportar.status()

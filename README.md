# TCF_mapping
Mapping terrestrial carbon fluxes TCF (GPP and NPP)

Author: Pablo Reyes-Muñoz

Code: Pablo Reyes-Muñoz

Workflow for mapping TCF from the synergy of Sentinel-3, Sentinel-5P and ERA-5 through Google Earth Engine, from the paper "Inferring global terrestrial carbon fluxes from the synergy of Sentinel 3 & 5P with Gaussian process hybrid models".

<ol style='list-style-type:disc'> 
  <li> Please, click the link below to get access to the Google Colab repo (a GEE account is required): 
    https://colab.research.google.com/drive/1ssVOAJmRuz1P44rQmABOMWuxOFboCIQZ?usp=sharing </li>
  
  </br>
    
  The code is formed by a set of Python functions as shown in the Google colab example
  
  <li> Define the location of your predictors inputs data sets (S3 vegetation, TROPOSIF and ERA-5-LAND) </li>
  
  </br>
  
  <p style="text-align:center;"> <img src="https://user-images.githubusercontent.com/8297994/219678537-e97d40d3-8825-4534-8705-b2be0e4805bb.png" alt="Repo"> </p>

  
  <li>  </li>
  
  </br>
  
  <li> Run all the ancillary functions. </li>
  
  </br>
  
  <li> The compose_image function format the predictors input for the GPR function below </li>
  
  </br>

  <li> Calculate_Green function is the core of the GPR algorithm implemented in GEE </li>

  <\br>

  <li> The map_loop function iterates over the defined temporal windows  </li>

  <\br>
  
  <p style="text-align:center;"> <img src="https://user-images.githubusercontent.com/8297994/219683269-1ad8df5b-0f00-4a10-897d-7e1c6877e9b1.png"></p> 

  </br>
  
</ol>

For <b> training and exporting customized models from ARTMO to GEE </b>, please follow the guidelines in https://github.com/msalinero/ARTMOtoGEE.git

A workflow in Python to produce <b> time series mapping </b> over a region of interest can be found in <a href="https://colab.research.google.com/github/daviddkovacs/Global-EVT-maps/blob/main/Main%20Python%20script.ipynb"> this link</a>

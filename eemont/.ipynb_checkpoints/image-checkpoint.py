import ee
import warnings

def _extend_eeImage():
    """Decorator. Extends the ee.ImageCollection class."""
    return lambda f: (setattr(ee.image.Image,f.__name__,f) or f)

def _get_platform(img):
    '''Gets the platform (satellite) of an image and wheter if it is a Surface Reflectance product.
    
    Parameters
    ----------
    img : ee.Image [this]
        Image to get platform.
        
    Returns
    -------
    dict
        Platform and product of the image.
    '''
    platforms = [
        'COPERNICUS/S3',
        'COPERNICUS/S2',
        'LANDSAT/LC08',
        'LANDSAT/LE07',
        'LANDSAT/LT05',
        'LANDSAT/LT04',
        'MODIS/006/MCD43A4',
        'MODIS/006/MCD43A3',
        'MODIS/006/MOD09GQ',
        'MODIS/006/MOD10A1',
        'MODIS/006/MOD11A1',
        'MODIS/006/MOD09GA',
        'MODIS/006/MODOCGA',
        'MODIS/006/MOD14A1',
        'MODIS/006/MCD43A1',
        'MODIS/006/MCD15A3H',
        'MODIS/006/MOD09Q1',
        'MODIS/006/MOD09A1',
        'MODIS/006/MOD11A2',
        'MODIS/006/MOD17A2H',
        'MODIS/006/MOD16A2',
        'MODIS/006/MOD13Q1',
        'MODIS/006/MOD13A1',
        'MODIS/006/MOD13A2',
        'MODIS/061/MOD08_M3',
        'MODIS/006/MOD17A3HGF'
    ]
    
    imgID = img.get('system:id').getInfo()
    plt = None
    
    for platform in platforms:
        if platform in imgID:
            plt = platform
        if '_SR' in imgID:
            platformDict = {'platform': plt, 'sr': True}
        else:
            platformDict = {'platform': plt, 'sr': False}
            
    if plt is None:
        raise Exception("Sorry, satellite platform not supported!")
            
    return platformDict

@_extend_eeImage()
def index(self,index = 'NDVI',G = 2.5,C1 = 6.0,C2 = 7.5,L = 1.0):
    '''Computes one or more spectral indices (indices are added as bands) for an image.
    
    Parameters
    ----------    
    self : ee.Image [this]
        Image to compute indices on. Must be scaled to [0,1]. Check the supported platforms in User Guide > Spectral Indices Computation.        
    index : string | list[string], default = 'NDVI'
        Index or list of indices to compute.\n
        Available options:
            - 'vegetation' : Compute all vegetation indices.
            - 'burn' : Compute all burn indices.
            - 'water' : Compute all water indices.
            - 'all' : Compute all indices listed below.
        Vegetation indices:
            - 'BNDVI' : Blue Normalized Difference Vegetation Index.
            - 'CIG' : Chlorophyll Index - Green.
            - 'CVI' : Chlorophyll Vegetation Index.
            - 'EVI' : Enhanced Vegetation Index.
            - 'GNDVI' : Green Normalized Difference Vegetation Index.
            - 'NDVI' : Normalized Difference Vegetation Index.
            - 'NGRDI' : Normalized Green Red Difference Index.        
            - 'SAVI' : Soil-Adjusted Vegetation Index.
            - 'SR' : Simple Ratio.
        Burn and fire indices:     
            - 'BAI' : Burned Area Index.
            - 'BAIS2' : Burned Area Index for Sentinel 2.
            - 'NBR' : Normalized Burn Ratio.
        Water indices:            
            - 'MNDWI' : Modified Normalized Difference Water Index.
            - 'NDWI' : Normalized Difference Water Index.        
    G : float, default = 2.5
        Gain factor. Used just for index = 'EVI'. 
    C1 : float, default = 6.0
        Coefficient 1 for the aerosol resistance term. Used just for index = 'EVI'.
    C2 : float, default = 7.5
        Coefficient 2 for the aerosol resistance term. Used just for index = 'EVI'.
    L : float, default = 1.0
        Canopy background adjustment. Used just for index = ['EVI','SAVI'].
        
    Returns
    -------
    ee.Image
        Image with the computed spectral index, or indices, as new bands.
    '''  
    platformDict = _get_platform(self)
    
    def lookupDic(img):
        
        def lookupS2(img):
            return {
                'G': float(G),
                'C1': float(C1),
                'C2': float(C2),
                'L': float(L),
                'A': img.select('B1'),
                'B': img.select('B2'),
                'G': img.select('B3'),
                'R': img.select('B4'),
                'RE1': img.select('B5'),
                'RE2': img.select('B6'),
                'RE3': img.select('B7'),
                'N' : img.select('B8'),
                'RE4': img.select('B8A'),
                'WV' : img.select('B9'),            
                'S1': img.select('B11'),
                'S2': img.select('B12')
            }
        
        def lookupL8(img):
            return {
                'G': float(G),
                'C1': float(C1),
                'C2': float(C2),
                'L': float(L),
                'A': img.select('B1'),
                'B': img.select('B2'),
                'G': img.select('B3'),
                'R': img.select('B4'),
                'N': img.select('B5'),
                'S1': img.select('B6'),
                'S2': img.select('B7'),                
                'T1' : img.select('B10'),
                'T2': img.select('B11')
            }
        
        def lookupL457(img):
            return {
                'G': float(G),
                'C1': float(C1),
                'C2': float(C2),
                'L': float(L),
                'B': img.select('B1'),
                'G': img.select('B2'),
                'R': img.select('B3'),
                'N': img.select('B4'),
                'S1': img.select('B5'),
                'T1': img.select('B6'),
                'S2': img.select('B7')                
            }
        
        lookupPlatform = {
            'COPERNICUS/S2': lookupS2,
            'LANDSAT/LC08': lookupL8,
            'LANDSAT/LE07': lookupL457,
            'LANDSAT/LT05': lookupL457,
            'LANDSAT/LT04': lookupL457
        }
        
        if platformDict['platform'] not in list(lookupPlatform.keys()):
            raise Exception("Sorry, satellite platform not supported for index computation!")
        
        return lookupPlatform[platformDict['platform']](img)
    
    # VEGETATION INDICES
    
    def BNDVI(img):
        return img.addBands(img.expression('(N - B) / (N + B)',lookupDic(img)).rename('BNDVI'))
    
    def CIG(img):
        return img.addBands(img.expression('(N / G) - 1',lookupDic(img)).rename('CIG'))
    
    def CVI(img):
        return img.addBands(img.expression('(N * R) / (G ** 2)',lookupDic(img)).rename('CVI'))
    
    def EVI(img):
        return img.addBands(img.expression('G * (N - R) / (N + C1 * R - C2 * B + L)',lookupDic(img)).rename('EVI'))
       
    def GNDVI(img):
        return img.addBands(img.expression('(N - G) / (N + G)',lookupDic(img)).rename('GNDVI'))
    
    def NDVI(img):
        return img.addBands(img.expression('(N - R) / (N + R)',lookupDic(img)).rename('NDVI'))
    
    def NGRDI(img):
        return img.addBands(img.expression('(G - R) / (G + R)',lookupDic(img)).rename('NGRDI'))
    
    def SAVI(img):
        return img.addBands(img.expression('(1 + L) * (N - R) / (N + R + L)',lookupDic(img)).rename('SAVI'))
    
    def SR(img):
        return img.addBands(img.expression('N / R',lookupDic(img)).rename('SR'))
    
    lookupVegetation = {
        'BNDVI': BNDVI,
        'CIG': CIG,
        'CVI': CVI,
        'EVI': EVI,
        'GNDVI': GNDVI,
        'NDVI': NDVI,
        'NGRDI': NGRDI,        
        'SAVI': SAVI,
        'SR': SR
    }
    
    # BURN INDICES
    
    def BAI(img):
        return img.addBands(img.expression('1.0 / ((0.1 - R) ** 2.0 + (0.06 - N) ** 2.0)',lookupDic(img)).rename('BAI'))
    
    def BAIS2(img):
        first = img.expression('(1.0 - ((RE2 * RE3 * RE4) / R) ** 0.5)',lookupDic(img))
        second = img.expression('(((S2 - RE4)/(S2 + RE4) ** 0.5) + 1.0)',lookupDic(img))
        return img.addBands(first.multiply(second).rename('BAIS2'))
    
    def NBR(img):
        return img.addBands(img.expression('(N - S2) / (N + S2)',lookupDic(img)).rename('NBR'))
    
    lookupBurn = {
        'BAI': BAI,
        'BAIS2': BAIS2,
        'NBR': NBR
    }
    
    # WATER INDICES
        
    def MNDWI(img):
        return img.addBands(img.expression('(G - S1) / (G + S1)',lookupDic(img)).rename('MNDWI'))
    
    def NDWI(img):
        return img.addBands(img.expression('(G - N) / (G + N)',lookupDic(img)).rename('NDWI'))
    
    lookupWater = {
        'MNDWI': MNDWI,
        'NDWI': NDWI,
    }
    
    # ALL INDICES
    
    lookup = {**lookupVegetation, **lookupBurn, **lookupWater}
    
    if not isinstance(index, list):
        if index == 'all':
            index = list(lookup.keys())
        elif index == 'vegetation':
            index = list(lookupVegetation.keys())
        elif index == 'burn':
            index = list(lookupBurn.keys())
        elif index == 'water':
            index = list(lookupWater.keys())
        else:
            index = [index]        
    
    listOfIndices = list(lookup.keys())
    listOfIndicesLandsat = list(listOfIndices)
    listOfIndicesLandsat.remove('BAIS2')
    
    lookupIndicesPlatform = {
        'COPERNICUS/S2': listOfIndices,
        'LANDSAT/LC08': listOfIndicesLandsat,
        'LANDSAT/LE07': listOfIndicesLandsat,
        'LANDSAT/LT05': listOfIndicesLandsat,
        'LANDSAT/LT04': listOfIndicesLandsat
    }
    
    for idx in index:
        if idx not in list(lookup.keys()):
            warnings.warn("Index " + idx + " is not a built-in index and it won't be computed!",Warning)
        elif idx not in lookupIndicesPlatform[platformDict['platform']]:
            warnings.warn("Index " + idx + " can't be computed for this platform!",Warning)
        else:
            self = lookup[idx](self)
        
    return self

@_extend_eeImage()
def maskClouds(self, method = 'cloud_prob', prob = 60, maskCirrus = True, maskShadows = True, scaledImage = False, dark = 0.15, cloudDist = 1000, buffer = 250, cdi = None):
    '''Masks clouds and shadows in an image (valid just for Surface Reflectance products).
    
    Parameters
    ----------    
    self : ee.Image [this]
        Image to mask. Check the supported platforms in User Guide > Masking Clouds and Shadows.
    method : string, default = 'cloud_prob'
        Method used to mask clouds.\n
        Available options:
            - 'cloud_prob' : Use cloud probability.
            - 'qa' : Use Quality Assessment band.
        This parameter is ignored for Landsat products.
    prob : numeric [0, 100], default = 60
        Cloud probability threshold. Valid just for method = 'prob'. This parameter is ignored for Landsat products.
    maskCirrus : boolean, default = True
        Whether to mask cirrus clouds. Valid just for method = 'qa'. This parameter is ignored for Landsat products.
    maskShadows : boolean, default = True
        Whether to mask cloud shadows. For more info see 'Braaten, J. 2020. Sentinel-2 Cloud Masking with s2cloudless. Google Earth Engine, Community Tutorials'.
    scaledImage : boolean, default = False
        Whether the pixel values are scaled to the range [0,1] (reflectance values). This parameter is ignored for Landsat products.
    dark : float [0,1], default = 0.15
        NIR threshold. NIR values below this threshold are potential cloud shadows. This parameter is ignored for Landsat products.
    cloudDist : int, default = 1000
        Maximum distance in meters (m) to look for cloud shadows from cloud edges. This parameter is ignored for Landsat products.
    buffer : int, default = 250
        Distance in meters (m) to dilate cloud and cloud shadows objects. This parameter is ignored for Landsat products.
    cdi : float [-1,1], default = None
        Cloud Displacement Index threshold. Values below this threshold are considered potential clouds. 
        A cdi = None means that the index is not used. For more info see 'Frantz, D., HaS, E., Uhl, A., Stoffels, J., Hill, J. 2018. Improvement of the Fmask algorithm for Sentinel-2 images:
        Separating clouds from bright surfaces based on parallax effects. Remote Sensing of Environment 2015: 471-481'.
        This parameter is ignored for Landsat products.
        
    Returns
    -------
    ee.Image
        Cloud-shadow masked image.
    '''
    def S3(args):
        qa = args.select('quality_flags')
        notCloud = qa.bitwiseAnd(1 << 27).eq(0);
        return args.updateMask(notCloud)
    
    def S2(args):    

        def cloud_prob(img):
            clouds = ee.Image(img.get('cloud_mask')).select('probability')
            isCloud = clouds.gte(prob).rename('CLOUD_MASK')
            return img.addBands(isCloud)

        def QA(img):
            qa = img.select('QA60')
            cloudBitMask = 1 << 10    
            isCloud = qa.bitwiseAnd(cloudBitMask).eq(0)
            if maskCirrus:
                cirrusBitMask = 1 << 11
                isCloud = isCloud.And(qa.bitwiseAnd(cirrusBitMask).eq(0))
            isCloud = isCloud.Not().rename('CLOUD_MASK')
            return img.addBands(isCloud)

        def CDI(img):
            idx = img.get('system:index')
            S2TOA = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.eq('system:index',idx)).first()
            CloudDisplacementIndex = ee.Algorithms.Sentinel2.CDI(S2TOA)
            isCloud = CloudDisplacementIndex.lt(cdi).rename('CLOUD_MASK_CDI')
            return img.addBands(isCloud)

        def get_shadows(img):      
            notWater = img.select('SCL').neq(6)
            if not scaledImage:
                darkPixels = img.select('B8').lt(dark * 1e4).multiply(notWater)
            else:  
                darkPixels = img.select('B8').lt(dark).multiply(notWater)        
            shadowAzimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')))        
            cloudProjection = img.select('CLOUD_MASK').directionalDistanceTransform(shadowAzimuth,cloudDist/10)
            cloudProjection = cloudProjection.reproject(crs = img.select(0).projection(),scale = 10).select('distance').mask()            
            isShadow = cloudProjection.multiply(darkPixels).rename('SHADOW_MASK')        
            return img.addBands(isShadow)

        def clean_dilate(img):        
            isCloudShadow = img.select('CLOUD_MASK')
            if cdi != None:
                isCloudShadow = isCloudShadow.And(img.select('CLOUD_MASK_CDI'))
            if maskShadows:
                isCloudShadow = isCloudShadow.add(img.select('SHADOW_MASK')).gt(0)        
            isCloudShadow = isCloudShadow.focal_min(20,units = 'meters').focal_max(buffer*2/10,units = 'meters').rename('CLOUD_SHADOW_MASK')
            return img.addBands(isCloudShadow)

        def apply_mask(img):
            return img.updateMask(img.select('CLOUD_SHADOW_MASK').Not())
        
        if method == 'cloud_prob':
            S2Clouds = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
            fil = ee.Filter.equals(leftField = 'system:index',rightField = 'system:index')
            S2WithCloudMask = ee.Join.saveFirst('cloud_mask').apply(ee.ImageCollection(args),S2Clouds,fil)
            S2Masked = ee.ImageCollection(S2WithCloudMask).map(cloud_prob).first()            
        elif method == 'qa':        
            S2Masked = QA(args)
        if cdi != None:
            S2Masked = CDI(S2Masked)
        if maskShadows:
            S2Masked = get_shadows(S2Masked)
        S2Masked = apply_mask(clean_dilate(S2Masked))        
        
        return S2Masked
    
    def L8(args):        
        cloudsBitMask = (1 << 5)
        qa = args.select('pixel_qa')
        mask = qa.bitwiseAnd(cloudsBitMask).eq(0)
        if maskShadows:
            cloudShadowBitMask = (1 << 3)
            mask = mask.And(qa.bitwiseAnd(cloudShadowBitMask).eq(0))
        return args.updateMask(mask)

    def L457(args):
        qa = args.select('pixel_qa')
        cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7))
        if maskShadows:
            cloud = cloud.Or(qa.bitwiseAnd(1 << 3))
        mask2 = args.mask().reduce(ee.Reducer.min());
        return args.updateMask(cloud.Not()).updateMask(mask2);
    
    def MOD09GA(args):
        qa = args.select('state_1km')
        notCloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 8).eq(0))        
        return args.updateMask(notCloud);
    
    def MCD15A3H(args):
        qa = args.select('FparExtra_QC')
        notCloud = qa.bitwiseAnd(1 << 5).eq(0)
        if maskShadows:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 6).eq(0))
        if maskCirrus:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 4).eq(0))        
        return args.updateMask(notCloud);
    
    def MOD09Q1(args):
        qa = args.select('State')
        notCloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 8).eq(0))        
        return args.updateMask(notCloud);
        
    def MOD09A1(args):
        qa = args.select('StateQA')
        notCloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            notCloud = notCloud.And(qa.bitwiseAnd(1 << 8).eq(0))        
        return args.updateMask(notCloud)
    
    def MOD17A2H(args):
        qa = args.select('Psn_QC')
        notCloud = qa.bitwiseAnd(1 << 3).eq(0)
        return args.updateMask(notCloud)
    
    def MOD16A2(args):
        qa = args.select('ET_QC')
        notCloud = qa.bitwiseAnd(1 << 3).eq(0)
        return args.updateMask(notCloud)
    
    def MOD13Q1A1(args):
        qa = args.select('SummaryQA')
        notCloud = qa.bitwiseAnd(1 << 0).eq(0)
        return args.updateMask(notCloud)
    
    def MOD13A2(args):
        qa = args.select('SummaryQA')
        notCloud = qa.eq(0)
        return args.updateMask(notCloud)
    
    lookup = {
        'COPERNICUS/S3': S3,
        'COPERNICUS/S2': S2,
        'LANDSAT/LC08': L8,
        'LANDSAT/LE07': L457,
        'LANDSAT/LT05': L457,
        'LANDSAT/LT04': L457,
        'MODIS/006/MOD09GA': MOD09GA,
        'MODIS/006/MCD15A3H': MCD15A3H,
        'MODIS/006/MOD09Q1': MOD09Q1,
        'MODIS/006/MOD09A1': MOD09A1,
        'MODIS/006/MOD17A2H': MOD17A2H,
        'MODIS/006/MOD16A2': MOD16A2,
        'MODIS/006/MOD13Q1': MOD13Q1A1,
        'MODIS/006/MOD13A1': MOD13Q1A1,
        'MODIS/006/MOD13A2': MOD13A2
    }
    
    platformDict = _get_platform(self)
    
    if platformDict['platform'] not in list(lookup.keys()):
        raise Exception("Sorry, satellite platform not supported for cloud masking!")
    
    maskedImage = lookup[platformDict['platform']](self)    
    
    return maskedImage

@_extend_eeImage()
def scale(self):    
    '''Scales bands on an image.
    
    Parameters
    ----------    
    self : ee.Image [this]
        Image to scale. Check the supported platforms in User Guide > Image Scaling.
        
    Returns
    -------
    ee.Image
        Scaled image.
    '''
    def S3(img):
        scalars = [
            0.0139465,
            0.0133873,
            0.0121481,
            0.0115198,
            0.0100953,
            0.0123538,
            0.00879161,
            0.00876539,
            0.0095103,
            0.00773378,
            0.00675523,
            0.0071996,
            0.00749684,
            0.0086512,
            0.00526779,
            0.00530267,
            0.00493004,
            0.00549962,
            0.00502847,
            0.00326378,
            0.00324118
        ]
        scaled = img.select(['Oa.*']).multiply(scalars).addBands(img.select('quality_flags'))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def S2(img):
        scaled = img.select(['B.*']).divide(1e4)      
        scaled = scaled.addBands(img.select(['Q.*']))
        if platformDict['sr']:            
            scaled = scaled.addBands(img.select(['AOT','WVP']).divide(1e3))
            scaled = scaled.addBands(img.select(['T.*']))            
            scaled = scaled.addBands(img.select('SCL'))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def L8(img):               
        if platformDict['sr']:
            scaled = img.select(['B[1-9]']).divide(1e4)
            scaled = scaled.addBands(img.select(['B10','B11']).divide(10)) 
            scaled = scaled.addBands(img.select(['sr_aerosol','pixel_qa','radsat_qa']))
            return ee.Image(scaled.copyProperties(img,img.propertyNames()))
        else:
            warnings.warn("TOA reflectance for Landsat 8 is already scaled!",Warning)
            pass
        
    def L457(img):               
        if platformDict['sr']:
            scaled = img.select(['B[1-5]','B7']).divide(1e4)
            scaled = scaled.addBands(img.select(['B6']).divide(10)) 
            scaled = scaled.addBands(img.select(['sr_atmos_opacity']).divide(1e3)) 
            scaled = scaled.addBands(img.select(['sr_cloud_qa','pixel_qa','radsat_qa']))
            return ee.Image(scaled.copyProperties(img,img.propertyNames()))
        else:
            warnings.warn("TOA reflectance for Landsat 4, 5 and 7 is already scaled!",Warning)
            pass
    
    def MCD43A4(img):
        scaled = img.select(['Nadir.*']).divide(1e4)      
        scaled = scaled.addBands(img.select(['BRDF.*']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MCD43A3(img):
        scaled = img.select(['Albedo.*']).divide(1e3)      
        scaled = scaled.addBands(img.select(['BRDF.*']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD09GQ(img):
        scaled = img.select(['sur.*']).divide(1e4)
        scaled = scaled.addBands(img.select(['obscov']).divide(100)) 
        scaled = scaled.addBands(img.select(['num_observations','QC_250m','iobs_res','orbit_pnt','granule_pnt']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD10A1(img):
        scaled = img.select(['NDSI']).divide(1e4)      
        scaled = scaled.addBands(img.select(['NDSI_Snow.*']))
        scaled = scaled.addBands(img.select(['Snow.*']))
        scaled = scaled.addBands(img.select(['orbit_pnt','granule_pnt']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD11A1(img):
        scaled = img.select(['LST.*']).multiply(0.02)
        scaled = scaled.addBands(img.select(['Day_view_time','Night_view_time']).multiply(0.1)) 
        scaled = scaled.addBands(img.select(['Emis.*']).multiply(0.002)) 
        scaled = scaled.addBands(img.select(['Clear.*']).multiply(0.0005))
        scaled = scaled.addBands(img.select(['QC_Day','Day_view_angle','QC_Night','Night_view_angle']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD09GA(img):
        scaled = img.select(['sur.*']).multiply(0.0001)        
        scaled = scaled.addBands(img.select(['Sensor.*']).multiply(0.01)) 
        scaled = scaled.addBands(img.select(['Solar.*']).multiply(0.01)) 
        scaled = scaled.addBands(img.select(['Range']).multiply(25))
        scaled = scaled.addBands(img.select(['num_observations_1km','state_1km','gflags','orbit_pnt','granule_pnt','num_observations_500m','QC_500m','obscov_500m','iobs_res','q_scan']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MODOCGA(img):
        scaled = img.select(['sur.*']).multiply(0.0001)  
        scaled = scaled.addBands(img.select(['num_observations','orbit_pnt','granule_pnt']))
        scaled = scaled.addBands(img.select(['QC.*']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD14A1(img):
        scaled = img.select(['MaxFRP']).multiply(0.1)  
        scaled = scaled.addBands(img.select(['FireMask','sample','QA']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MCD43A1(img):
        scaled = img.select(['BRDF_Albedo_Parameters.*']).multiply(0.001)  
        scaled = scaled.addBands(img.select(['BRDF_Albedo_Band.*']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MCD15A3H(img):
        scaled = img.select(['Fpar','FparStdDev']).multiply(0.01)  
        scaled = scaled.addBands(img.select(['Lai','LaiStdDev']).multiply(0.1)) 
        scaled = scaled.addBands(img.select(['FparLai_QC','FparExtra_QC']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD09Q1(img):
        scaled = img.select(['sur.*']).divide(1e4)        
        scaled = scaled.addBands(img.select(['State','QA']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD09A1(img):
        scaled = img.select(['sur.*']).divide(1e4)
        scaled = scaled.addBands(img.select(['SolarZenith','ViewZenith','RelativeAzimuth']).multiply(0.01)) 
        scaled = scaled.addBands(img.select(['QA','StateQA','DayOfYear']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD11A2(img):
        scaled = img.select(['LST.*']).multiply(0.02)
        scaled = scaled.addBands(img.select(['Day_view_time','Night_view_time']).multiply(0.1)) 
        scaled = scaled.addBands(img.select(['Emis.*']).multiply(0.002).add(0.49)) 
        scaled = scaled.addBands(img.select(['Day_view_angl','Night_view_angl']).subtract(65))
        scaled = scaled.addBands(img.select(['QC_Day','QC_Night','Clear_sky_days','Clear_sky_nights']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD17A2H(img):
        scaled = img.select(['Gpp','PsnNet']).multiply(0.0001)
        scaled = scaled.addBands(img.select(['Psn_QC']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD16A2(img):
        scaled = img.select(['ET','PET']).multiply(0.1)
        scaled = scaled.addBands(img.select(['LE','PLE']).multiply(0.0001))
        scaled = scaled.addBands(img.select(['ET_QC']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD13Q1(img):
        scaled = img.select(['NDVI','EVI']).multiply(0.0001)
        scaled = scaled.addBands(img.select(['sur.*']).multiply(0.0001))
        scaled = scaled.addBands(img.select(['ViewZenith','SolarZenith','RelativeAzimuth']).multiply(0.01))
        scaled = scaled.addBands(img.select(['DetailedQA','DayOfYear','SummaryQA']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD13A1(img):
        scaled = img.select(['NDVI','EVI']).multiply(0.0001)
        scaled = scaled.addBands(img.select(['sur.*']).multiply(0.0001))
        scaled = scaled.addBands(img.select(['ViewZenith','SolarZenith','RelativeAzimuth']).multiply(0.01))
        scaled = scaled.addBands(img.select(['DetailedQA','DayOfYear','SummaryQA']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD13A2(img):
        scaled = img.select(['NDVI','EVI']).multiply(0.0001)
        scaled = scaled.addBands(img.select(['sur.*']).multiply(0.0001))
        scaled = scaled.addBands(img.select(['ViewZenith','SolarZenith','RelativeAzimuth']).multiply(0.01))
        scaled = scaled.addBands(img.select(['DetailedQA','DayOfYear','SummaryQA']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD08_M3(img):
        scaled = img.select(['Aerosol.*']).multiply(0.001)
        scaled = scaled.addBands(img.select(['Cirrus.*']).multiply(0.0001))
        scaled = scaled.addBands(img.select(['Cloud_Optical_Thickness_Liquid_Log.*']).multiply(0.001))
        scaled = scaled.addBands(img.select(['Cloud_Optical_Thickness_Liquid_Mean_Uncertainty']).multiply(0.01))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    def MOD17A3HGF(img):
        scaled = img.select(['Npp']).multiply(0.0001)
        scaled = scaled.addBands(img.select(['Npp_QC']))
        return ee.Image(scaled.copyProperties(img,img.propertyNames()))
    
    lookup = {
        'COPERNICUS/S3': S3,
        'COPERNICUS/S2': S2,
        'LANDSAT/LC08': L8,
        'LANDSAT/LE07': L457,
        'LANDSAT/LT05': L457,
        'LANDSAT/LT04': L457,
        'MODIS/006/MCD43A4': MCD43A4,
        'MODIS/006/MCD43A3': MCD43A3,
        'MODIS/006/MOD09GQ': MOD09GQ,
        'MODIS/006/MOD10A1': MOD10A1,
        'MODIS/006/MOD11A1': MOD11A1,
        'MODIS/006/MOD09GA': MOD09GA,
        'MODIS/006/MODOCGA': MODOCGA,
        'MODIS/006/MOD14A1': MOD14A1,
        'MODIS/006/MCD43A1': MCD43A1,
        'MODIS/006/MCD15A3H': MCD15A3H,
        'MODIS/006/MOD09Q1': MOD09Q1,
        'MODIS/006/MOD09A1': MOD09A1,
        'MODIS/006/MOD11A2': MOD11A2,
        'MODIS/006/MOD17A2H': MOD17A2H,
        'MODIS/006/MOD16A2': MOD16A2,
        'MODIS/006/MOD13Q1': MOD13Q1,
        'MODIS/006/MOD13A1': MOD13A1,
        'MODIS/006/MOD13A2': MOD13A2,
        'MODIS/061/MOD08_M3': MOD08_M3,
        'MODIS/006/MOD17A3HGF': MOD17A3HGF
    }
    
    platformDict = _get_platform(self)    
    
    if platformDict['platform'] not in list(lookup.keys()):
        raise Exception("Sorry, satellite platform not supported for scaling!")
    
    scaledImage = lookup[platformDict['platform']](self)
    
    return scaledImage
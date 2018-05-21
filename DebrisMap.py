from __future__ import division
# function called by DebrisCoverTools.py
# By Sam Herreid
#
def DebrisMap(workspace, data_dir, landsat, shp_dir, mask_dir, A_remove, A_fill, Want_CloudRemoval):
    print 'Running: DebrisMap...'
    import arcpy
    from arcpy.sa import ExtractByMask, SetNull, Int
    import arcpy.cartography as CA
    import os
    out_dir = workspace
    arcpy.CheckOutExtension('Spatial')
    arcpy.CheckOutExtension('3D')

    #file name convention: (glacier name)_---y(year)---d(day of year)_---t(integer threshold *100)----r(area removed in m2)----f(area filled in m2)
    # t = threshold
    # r = area removed m2
    # f = area filled m2
    #e.g.: DeltaRange2010_2015y249d_145t2700r2700f.TIF
    
    if landsat == 5:
        Lband = '_b4.tif'
        Hband = '_b5.tif'
        threshold = 1.45 # Landsat TM threshold from Herreid et al., 2015
    elif landsat == 7:
        Lband = '_b4.tif'
        Hband = '_b5.tif'
        threshold = 1.45 # Landsat TM threshold from Herreid et al., 2015
    elif landsat == 8:
        Lband = '_b5.tif'
        Hband = '_b6.tif'
        threshold = 1.57 #1.2#Canwell # Landsat8 threshold from Herreid et al., 2015
    else:
        print 'Satellite not defined as Landsat5, 7 or 8'

    def glacier_debris(band_4, band_5, glacier_outline, out_dir):
        print 'Running glacier_debris'
        if Want_CloudRemoval == 'True':
            outExtractByMask = ExtractByMask(band_4, mask_dir + '\\' + band_4.split('\\')[-1].split('_b')[0][0:16] + band_4.split('\\')[-1].split('_b')[0][17:21] + 'mask.shp')
            outExtractByMask.save('del_nodatagone4.TIF')
            outExtractByMask = ExtractByMask(band_5, mask_dir + '\\' + band_4.split('\\')[-1].split('_b')[0][0:16] + band_4.split('\\')[-1].split('_b')[0][17:21] + 'mask.shp')
            outExtractByMask.save('del_nodatagone5.TIF')
            outExtractByMask = ExtractByMask('del_nodatagone4.TIF', glacier_outline)
            outExtractByMask.save('del_mask4.TIF')
            outExtractByMask = ExtractByMask('del_nodatagone5.TIF', glacier_outline)
            outExtractByMask.save('del_mask5.TIF')
            print 'extract'
        else:
            outExtractByMask = ExtractByMask(band_4, glacier_outline)
            outExtractByMask.save('del_mask4.TIF')
            outExtractByMask = ExtractByMask(band_5, glacier_outline)
            outExtractByMask.save('del_mask5.TIF')
            print 'extract'
        #Convert Raster to float for decimal threshold values
        arcpy.RasterToFloat_conversion('del_mask4.TIF', 'del_band_4a.flt')
        arcpy.RasterToFloat_conversion('del_mask5.TIF', 'del_band_5a.flt')
        arcpy.Divide_3d('del_band_4a.flt', 'del_band_5a.flt', 'del_division.TIF')
        print 'division'
        outSetNull = SetNull('del_division.TIF', 'del_division.TIF', 'VALUE > ' + str(threshold))

        #path to results folder, for loops add a counter if images are from the same year and day
        result_name = glacier_outline.split('.shp')[0].split('\\')[-1] + '_' + band_4.split('\\')[-1][9:13] + 'y' + band_4.split('\\')[-1][13:16] + 'd' + '_L' + band_4.split('\\')[-1][2:3] + '_' + Lband.split('_')[-1][1:2] + Hband.split('_')[-1][1:2] + 'b' + str(int(threshold * 100)) + 't' + str(A_remove) + 'r' + str(A_fill) + 'f'
        result_path = out_dir + glacier_outline.split('.shp')[0].split('\\')[-1] + '_' + band_4.split('\\')[-1][9:13] + 'y' + band_4.split('\\')[-1][13:16] + 'd' + '_L' + band_4.split('\\')[-1][2:3] + '_' + Lband.split('_')[-1][1:2] + Hband.split('_')[-1][1:2] + 'b' + str(int(threshold * 100)) + 't' + str(A_remove) + 'r' + str(A_fill) + 'f'

        if str(result_name + '1.shp' in os.listdir(out_dir)) == 'True':
            result_path = result_path + '2'
        elif str(result_name + '2.shp' in os.listdir(out_dir)) == 'True':
            result_path = result_path + '3'
        elif str(result_name + '3.shp' in os.listdir(out_dir)) == 'True':
            result_path = result_path + '4'
        elif str(result_name + '4.shp' in os.listdir(out_dir)) == 'True':
            result_path = result_path + '5'
        elif str(result_name + '5.shp' in os.listdir(out_dir)) == 'True':
            result_path = result_path + '6'
        else:
            result_path = result_path + '1'
            
        result_file = result_path + '.TIF'
        print 'result file: ' + result_file
        
        outSetNull.save(result_file)
        print 'Level 1 product produced'

        #Float raster to integer
        outInt = Int(result_file)
        outInt.save('del_result_file_int.TIF')
        # Set local variables
        inRaster = 'del_result_file_int.TIF'
        outPolygons = 'del_debris.shp'
        field = 'VALUE'
        arcpy.RasterToPolygon_conversion(inRaster, outPolygons, 'NO_SIMPLIFY', field)
        print 'to polygon'

        #Process: Dissolve. need to create "value" row where all elements=0
        arcpy.AddField_management('del_debris.shp', 'value', 'SHORT', 1, '', '', '', '', '')
        arcpy.Dissolve_management('del_debris.shp', 'del_debris_dissolve.shp', 'value')
        print 'dissolve'
        # Run the tool to create a new fc with only singlepart features
        arcpy.MultipartToSinglepart_management('del_debris_dissolve.shp', 'del_explode.shp')
        print 'explode'
        # Process: Calculate polygon area (km2)
        arcpy.CalculateAreas_stats('del_explode.shp', 'del_area.shp')
        arcpy.MakeFeatureLayer_management('del_area.shp', 'tempLayer')
        # Execute SelectLayerByAttribute to determine which features to delete
        expression = 'F_AREA <=' + str(A_remove) # m2
        arcpy.SelectLayerByAttribute_management('tempLayer', 'NEW_SELECTION', expression)
        arcpy.DeleteFeatures_management('tempLayer')
        print 'Shapes with an area <= ' + str(A_remove) + ' m2 removed; ' + str(A_remove / 900) + ' pixles, if 30m pixels'
        #Delete polygons < xx m2
        arcpy.Delete_management('tempLayer')
        print 'tempLayer deleted'
        result_file2 = result_path + '.shp'
        print 'Level 2 result file: ' + result_file2
        #Process: aggrigate (distance=1 m minimum area=0 minimum hole size=xx m: )
        CA.AggregatePolygons('del_area.shp', result_file2, 1, 0, A_fill, 'NON_ORTHOGONAL')
        print 'holes with an area <= ' + str(A_fill) + ' m2 filled/merged with debris polygon; ' + str(A_fill / 900) + ' pixles, if 30m pixels'

        rasterList = arcpy.ListRasters('*del*')
        for raster in rasterList:
            arcpy.Delete_management(raster)

        fcList = arcpy.ListFeatureClasses('*del*')
        for fc in fcList:
            arcpy.Delete_management(fc)

        print 'intermediate files deleted'
        print 'level 2 product produced'

    #get all satellite file names
    dirlist = os.listdir(data_dir)
    tiflist = []
    for item in dirlist:
        if item.lower().endswith(Hband):
            tiflist.append(item.split('_B')[0])

    #get all shape files
    dirlist = os.listdir(shp_dir)
    shplist = []
    for item in dirlist:
        if item.lower().endswith('shp'):
            arcpy.RepairGeometry_management(shp_dir + item)
            print 'glacier shapefile geometry repaired'
            shplist.append(item)

    print tiflist
    print shplist
    
    for glacier in shplist:
        for image in tiflist:
            glacier_debris(data_dir + image + Lband, data_dir + image + Hband, shp_dir + glacier, out_dir)

    dirlist = os.listdir(out_dir)
    resultlist = []
    for item in dirlist:
        if item.lower().endswith('shp'):
            resultlist.append(out_dir + item)

    arcpy.Merge_management(resultlist, out_dir + glacier.split('.shp')[0].split('\\')[-1] + '_mergeNoDissolve.shp')
    arcpy.Dissolve_management(out_dir + glacier.split('.shp')[0].split('\\')[-1] + '_mergeNoDissolve.shp', out_dir + glacier.split('.shp')[0].split('\\')[-1] + '_merged.shp')

    print 'merged shapefile created'
    print 'DebrisMap script complete'

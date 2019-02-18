from __future__ import division
# function called by DebrisCoverTools.py
# By Sam Herreid
#
def IceCliffLocation(workspace,dem,tileDebarea,pixel,minSlope,n_iterations,L_e,alpha,beta_e,A_min,phi,gamma):
    import sys
    import os
    import arcpy
    from arcpy import env
    from arcpy.sa import Slope, ExtractByMask, Raster, SetNull, Int
    import matplotlib.pyplot as plt
    import numpy as np
    from numpy import array
    from scipy.optimize import curve_fit
    env.overwriteOutput = True

    try:
        import arcinfo
    except:
        sys.exit("ArcInfo license not available")
        arcpy.AddMessage("ArcInfo license not available")
    if arcpy.CheckExtension("spatial") == "Available":
        arcpy.CheckOutExtension("spatial")
    else:
        sys.exit("Spatial Analyst license not available")
        arcpy.AddMessage("Spatial Analyst license not available")
        
    #Parameters that should be stable:
    slopeLimit = 90 # slope detection capped at this value
    
    ## Loop for optimizing slope
    if str(workspace.split("\\")[-1]) == 'Final':
        n = []
        n.append(minSlope)        
    else:
        minSlope = 0
        n = np.arange(minSlope,slopeLimit,(slopeLimit-minSlope)/n_iterations)

    skipIteration = []
    for minSlope in n:
        
        # check for existing iterations if code has previously run but crashed. 
        if arcpy.ListFeatureClasses("*cliffMap*"):
            fcListPrior = arcpy.ListFeatureClasses("*cliffMap*")
            skipIteration = []
            for prior_i in fcListPrior:
                if int(prior_i[14:16]) == int("%02d" % (int(minSlope),)):
                    skipIteration = 1
        if skipIteration == 1:
            continue

        ## Ice Cliff code  

        print 'IceCliffLocation script started...'
    
        # Parameter that probably should be 0
        minProb = 0 # probability associated with minSlope.
        
        arcpy.CopyFeatures_management(tileDebarea, workspace+"\\del_debarea.shp")
        debarea_iteration = workspace+"\\del_debarea.shp"
        arcpy.env.snapRaster = dem
        outExtractSlope = ExtractByMask(dem, debarea_iteration)

        outExtractSlope.save("dem_extract.TIF")
        if int(round(float(str(arcpy.GetRasterProperties_management(dem, "CELLSIZEX"))))) == pixel:
            dem = "dem_extract.TIF"
        else:    
            arcpy.Resample_management("dem_extract.TIF", "dem_extractResample.TIF", pixel, "NEAREST")
            arcpy.env.snapRaster = dem
            print "DEM resampeld from "+str(int(round(float(str(arcpy.GetRasterProperties_management(dem, "CELLSIZEX"))))))+' to '+str(pixel)
            dem = "dem_extractResample.TIF"
        
        # Create slope raster
        outSlope = Slope(dem, "DEGREE", 1)
        outSlope.save("del_slope.TIF")
    
        # Isolate slope values above minSlope 
        outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE <= "+ str(minSlope))
        outSetNull.save("del_minSlope.TIF")       
    
        # Exit process if no cliffs exist
        nocliff = arcpy.GetRasterProperties_management(Int("del_minSlope.TIF"), "ALLNODATA")
        if int(str(nocliff)) == 1:
            print "No area with a slope above "+str(minSlope)+"."
        elif float(str(arcpy.GetRasterProperties_management('del_minSlope.TIF',"MAXIMUM"))) - float(str(arcpy.GetRasterProperties_management('del_minSlope.TIF',"MINIMUM"))) == 0:
            print "Only one pixel with a slope above "+str(minSlope)+", iteration skipped."
        else:
            minMean = float(str(arcpy.GetRasterProperties_management("del_minSlope.TIF", "MEAN"))) 
            minSD = float(str(arcpy.GetRasterProperties_management("del_minSlope.TIF", "STD"))) 

            areaSlope = minMean
            
            print 'areaSlope = ' + str(areaSlope)
            
            # Isolate slope values above areaSlope 
            outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE <= "+ str(areaSlope))
            outSetNull.save("del_areaSlope.TIF")
            arcpy.env.snapRaster = dem  
                        
            # Exit process if no cliffs exist
            nocliff = arcpy.GetRasterProperties_management(Int("del_areaSlope.TIF"), "ALLNODATA")
            if int(str(nocliff)) == 1:
                print "No area with a slope above "+str(areaSlope)+"."
            elif float(str(arcpy.GetRasterProperties_management("del_areaSlope.TIF","MAXIMUM"))) - float(str(arcpy.GetRasterProperties_management("del_areaSlope.TIF","MINIMUM"))) == 0:
                print "Only one pixel with a slope above "+str(areaSlope)+", iteration skipped."
            else: 
                seedSlope = minMean+minSD 
                print 'seedSlope = ' + str(seedSlope)
                
                # Isolate slope values above areaSlope 
                outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE <= "+ str(seedSlope))
                outSetNull.save("del_seedSlope.TIF")

                # Exit process if no cliffs exist
                nocliff = arcpy.GetRasterProperties_management(Int("del_seedSlope.TIF"), "ALLNODATA")
                if int(str(nocliff)) == 1:
                    print "No seed area with a slope above "+str(seedSlope)+"."
                else:                    
                    # to int speeds up computation time
                    outInt = Int("del_areaSlope.TIF")
                    outInt.save("del_minSlopeInt.TIF")
                    outInt = Int("del_seedSlope.TIF")
                    outInt.save("del_seedSlopeInt.TIF")                  
                        
                    arcpy.RasterToPolygon_conversion("del_minSlopeInt.TIF", "del_minCliffSlope.shp", "NO_SIMPLIFY", "VALUE")
                    arcpy.AddField_management("del_minCliffSlope.shp", "value", "SHORT", 1, "", "", "", "", "")
                    arcpy.Dissolve_management("del_minCliffSlope.shp", "del_minCliff_dissolve.shp", "value")
                    arcpy.MultipartToSinglepart_management("del_minCliff_dissolve.shp", "del_minCliff_explode.shp")
                    arcpy.AddField_management("del_minCliff_explode.shp",'Area','FLOAT')
                    rows = arcpy.UpdateCursor("del_minCliff_explode.shp")
                    for row in rows:
                        areacliff = row.shape.area
                        row.Area = areacliff 
                        rows.updateRow(row)
                    del row, rows
                    arcpy.CopyFeatures_management("del_minCliff_explode.shp", "min"+str("%02d" % (minSlope,))+"_CliffArea.shp")
                    
                    arcpy.RasterToPolygon_conversion("del_seedSlopeInt.TIF", "del_seedSlope_dissolve.shp", "NO_SIMPLIFY", "VALUE")

                    # buffer in/out area to break up attached features
                    arcpy.Buffer_analysis("del_minCliff_explode.shp", "del_extendLineBuffer.shp", (pixel/2)-0.1, "FULL", "ROUND", "NONE")

                    # Generate ice cliff centerlines from Voronoi cells
                    if arcpy.management.GetCount("del_extendLineBuffer.shp")[0] == "0":
                        arcpy.CreateFeatureclass_management(workspace, 'del_lineAndArea_area.shp', "POLYGON","del_minCliff_dissolve.shp")
                        print "No area within the criteria defined by seed area value "+str(seedSlope)+", iteration stopped before centerlines."
                    else:
                        arcpy.FeatureToLine_management("del_extendLineBuffer.shp","del_line.shp","","ATTRIBUTES")
                        arcpy.Densify_edit("del_line.shp", "","5", "", "")
                        arcpy.FeatureVerticesToPoints_management ("del_line.shp", "del_verti.shp", "ALL")
                        arcpy.CreateThiessenPolygons_analysis("del_verti.shp","del_voronoiCells.shp" ,"ONLY_FID") 
                        arcpy.RepairGeometry_management("del_voronoiCells.shp")
                        arcpy.Clip_analysis("del_voronoiCells.shp", "del_extendLineBuffer.shp", "del_voronoiCellsClip.shp","") 
                        arcpy.FeatureToLine_management("del_voronoiCellsClip.shp","del_toLine.shp", "", attributes="ATTRIBUTES")
                        arcpy.MakeFeatureLayer_management("del_toLine.shp", "tempLayer", "", "", "")
                        arcpy.SelectLayerByLocation_management("tempLayer", "CROSSED_BY_THE_OUTLINE_OF","del_minCliff_explode.shp","","NEW_SELECTION")
                        arcpy.DeleteFeatures_management("tempLayer")
                        arcpy.Delete_management("tempLayer")
                        arcpy.Intersect_analysis(["del_toLine.shp",'del_minCliff_explode.shp'],"del_lineIntersect.shp")
                        arcpy.Dissolve_management("del_lineIntersect.shp", "del_toLineDis.shp", "", "", "SINGLE_PART", "DISSOLVE_LINES")
                        arcpy.UnsplitLine_management("del_toLineDis.shp","del_unsplit.shp","Id")
                        arcpy.MakeFeatureLayer_management("del_unsplit.shp", "tempLayer2", "", "", "")
                        arcpy.SelectLayerByLocation_management("tempLayer2", "BOUNDARY_TOUCHES","del_minCliff_explode.shp","","NEW_SELECTION")
                        arcpy.DeleteFeatures_management("tempLayer2")
                        arcpy.Delete_management("tempLayer2")
                        arcpy.cartography.SimplifyLine("del_unsplit.shp","del_clineSimpExp.shp","POINT_REMOVE",10)
                        arcpy.AddField_management("del_clineSimpExp.shp", "value", "SHORT", 1, "", "", "", "", "")
                        arcpy.Dissolve_management("del_clineSimpExp.shp", "del_clineSimp.shp", "value")
                        arcpy.TrimLine_edit("del_clineSimp.shp", "8 meters", "KEEP_SHORT")
                        arcpy.CopyFeatures_management("del_unsplit.shp", "min"+str("%02d" % (minSlope,))+"_Centerlines.shp")
                        
                        #refine centerline for final map
                        if arcpy.management.GetCount("del_clineSimp.shp")[0] == "0":
                            arcpy.CreateFeatureclass_management(workspace, 'del_lineAndArea_area.shp', "POLYGON","del_minCliff_dissolve.shp")
                            print "No area big enough to generate a centerline, iteration skipped."
                        else:                        
                        
                            # extend lines to capture cliff ends
                            count = 0
                            print "Extend line started..."
                            
                            jlist = [(pixel/2)-0.1] * int(round(L_e/(pixel/2)))
                            for j in jlist:
                                #create buffer out to set the limit a line will be extended to
                                arcpy.Buffer_analysis("del_clineSimp.shp", "del_clineSimpBuff1.shp", j, "FULL", "ROUND", "ALL")
                                arcpy.PolygonToLine_management("del_clineSimpBuff1.shp","del_clineSimpBuff1line.shp")
                                #merge centerline and bufferline
                                arcpy.Merge_management(["del_clineSimp.shp","del_clineSimpBuff1line.shp"], "del_clineSimpBuff1merge_dis.shp")
                                arcpy.Delete_management("del_clineSimp.shp")
                                print "Extend line "+str(count)+" started..."
                                arcpy.MultipartToSinglepart_management("del_clineSimpBuff1merge_dis.shp", "del_clineSimpBuff1merge.shp")
                                arcpy.MakeFeatureLayer_management("del_clineSimpBuff1merge.shp", "lineLayer", "", "", "")
                                arcpy.SelectLayerByLocation_management("lineLayer", "SHARE_A_LINE_SEGMENT_WITH", "del_clineSimpBuff1.shp", "", "NEW_SELECTION", "INVERT")
                                arcpy.ExtendLine_edit("del_clineSimpBuff1merge.shp", str(j+1)+" meters", "EXTENSION")
                                
                                #select share a line segment with buffer to remove buffer
                                 
                                arcpy.SelectLayerByLocation_management("lineLayer", "SHARE_A_LINE_SEGMENT_WITH", "del_clineSimpBuff1.shp", "", "NEW_SELECTION") 
                                arcpy.DeleteFeatures_management("lineLayer")
                                arcpy.Delete_management("lineLayer")
                                arcpy.CopyFeatures_management("del_clineSimpBuff1merge.shp", "del_clineSimp.shp")
                                arcpy.Delete_management("del_clineSimpBuff1.shp")
                                arcpy.Delete_management("del_clineSimpBuff1line.shp")
                                arcpy.Delete_management("del_clineSimpBuff1merge.shp")
                                count = count + j                                
                            del j, jlist
    
                            #remove last short ribs with a lenght threhold then reattach centerlines that may have been split
                            # calculate lenght of each centerline
                            if arcpy.management.GetCount("del_clineSimp.shp")[0] == "0":
                                arcpy.CreateFeatureclass_management(workspace, 'del_lineAndArea_area.shp', "POLYGON","del_minCliff_explode.shp")
                                print "Centerline shape empty, iteration skipped."
                            else:
                                arcpy.AddField_management("del_clineSimp.shp",'L','FLOAT')
                                rows = arcpy.UpdateCursor("del_clineSimp.shp")
                                for row in rows:
                                    areacliff = row.shape.length
                                    row.L = areacliff 
                                    rows.updateRow(row)
                                del row, rows
                                arcpy.CopyFeatures_management("del_clineSimp.shp", "min"+str("%02d" % (minSlope,))+"_extendedCenterlines.shp")
                                
                                # buffer out centerlines to capture end area removed in earlier buffer
                                arcpy.Buffer_analysis("del_clineSimp.shp", "del_CliffCenterlineOut.shp", ((alpha*pixel*(2**(1/2)))/2), "FULL", "ROUND", "NONE")
        
                                # define area with a slope less than that which defined "del_minCliff_dissolve.shp"
                                edgeAreaSlope = areaSlope-beta_e
                                print "Edge area defined by slope "+str(edgeAreaSlope)
                                outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE <= "+ str(edgeAreaSlope))
                                outSetNull.save("del_edgeSlope.TIF") 
                               
                                outInt = Int("del_edgeSlope.TIF")
                                outInt.save("del_edgeSlopeInt.TIF")                    
                                arcpy.RasterToPolygon_conversion("del_edgeSlopeInt.TIF", "del_edgeAreaSlope.shp", "NO_SIMPLIFY", "VALUE")
                                arcpy.AddField_management("del_edgeAreaSlope.shp", "value", "SHORT", 1, "", "", "", "", "")
                                arcpy.Dissolve_management("del_edgeAreaSlope.shp", "del_edgeAreaSlope_dissolve.shp", "value")
                                arcpy.CopyFeatures_management("del_edgeAreaSlope_dissolve.shp", "min"+str("%02d" % (minSlope,))+"_edgeArea.shp")
                                arcpy.Intersect_analysis (["del_edgeAreaSlope_dissolve.shp", "del_CliffCenterlineOut.shp"], "del_betaF_edgeArea.shp")
                    
                                # merge buffered lines with buffered area                    
                                arcpy.Merge_management(["del_betaF_edgeArea.shp", "del_minCliff_explode.shp"], "del_lineAndArea.shp")
                                arcpy.AddField_management("del_lineAndArea.shp", "valueDis", "SHORT", 1, "", "", "", "", "")                    
                                arcpy.Dissolve_management("del_lineAndArea.shp", "del_lineAndArea_dissolve1.shp", "valueDis")
                                # fill holes and remove shapes less than one pixel to avoid error from buffer tool
                                arcpy.MultipartToSinglepart_management("del_lineAndArea_dissolve1.shp", "del_lineAndArea_explode1.shp")
                                arcpy.CalculateAreas_stats("del_lineAndArea_explode1.shp", 'del_lineAndArea_area1.shp')
                                arcpy.MakeFeatureLayer_management('del_lineAndArea_area1.shp', 'tempLayer')
                                expression = 'F_AREA <' + str(pixel**2) # m2
                                arcpy.SelectLayerByAttribute_management('tempLayer', 'NEW_SELECTION', expression)
                                arcpy.DeleteFeatures_management('tempLayer')
                                arcpy.Delete_management('tempLayer')
                                arcpy.cartography.AggregatePolygons('del_lineAndArea_area1.shp', "del_lineAndArea_dissolve.shp", 1, 0, pixel**2, 'NON_ORTHOGONAL') 
                                                   
                                arcpy.RepairGeometry_management("del_lineAndArea_dissolve.shp")
                                # buffer in to reomve sliver geometries and out to make a diagonal set of single pixel shapes one feature
                                arcpy.Buffer_analysis("del_lineAndArea_dissolve.shp", "del_lineAndArea_dissolveSmallBufferIn.shp", -0.5, "FULL", "ROUND", "ALL")
                                arcpy.Buffer_analysis("del_lineAndArea_dissolveSmallBufferIn.shp", "del_lineAndArea_dissolveSmallBuffer.shp", 1, "FULL", "ROUND", "ALL")
                                arcpy.MultipartToSinglepart_management("del_lineAndArea_dissolveSmallBuffer.shp", "del_lineAndArea_explode.shp")
                                arcpy.CalculateAreas_stats('del_lineAndArea_explode.shp', 'del_lineAndArea_area.shp')
                                arcpy.MakeFeatureLayer_management('del_lineAndArea_area.shp', 'tempLayer')
                                expression = 'F_AREA <=' + str((pixel**2)*A_min)
                                arcpy.SelectLayerByAttribute_management('tempLayer', 'NEW_SELECTION', expression)
                                arcpy.DeleteFeatures_management('tempLayer')
                                arcpy.Delete_management('tempLayer')
                                
                                if arcpy.management.GetCount("del_lineAndArea_area.shp")[0] == "0":
                                    print "del_lineAndArea_area.shp empty, iteration stopped."
                                else:
                                    arcpy.AddField_management("del_lineAndArea_area.shp", "value", "SHORT", 1, "", "", "", "", "")
                                    arcpy.CopyFeatures_management('del_lineAndArea_area.shp', "min"+str("%02d" % (minSlope,))+"area"+str(int(areaSlope))+"_FinalCliffShape.shp")                         
                                                    
                            # CDF for values between minSlope and maxSlope
                            outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE >= "+ str(minSlope))
                            outSetNull.save("del_min.TIF")
                            arcpy.RasterToFloat_conversion("del_min.TIF", "del_min.flt")
                            minsl = Raster('del_min.flt')
                            slopemin = minsl*0.0
                            slopemin.save('del_minSl.TIF')            
                                
                            outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE > "+ str(seedSlope))
                            outSetNull = SetNull(outSetNull, outSetNull, "VALUE < "+ str(minSlope))
                            outSetNull.save("del_mid.TIF")
                            arcpy.RasterToFloat_conversion("del_mid.TIF", "del_mid.flt")
                            midsl = Raster('del_mid.flt')
                            b = (1-(((1-minProb)/(seedSlope-minSlope))*seedSlope))
                            slopemid = (((1-minProb)/(seedSlope-minSlope))*midsl)+b
                            arcpy.env.snapRaster = dem
                            slopemid.save('del_midSl.TIF')
                            arcpy.env.snapRaster = dem
            
                            outSetNull = SetNull("del_slope.TIF", "del_slope.TIF", "VALUE <= "+ str(seedSlope))
                            outSetNull.save("del_max.TIF")
                            arcpy.RasterToFloat_conversion("del_max.TIF", "del_max.flt")
                            maxsl = Raster('del_max.flt')
                            slopemax = maxsl*0.0+1.0
                            arcpy.env.snapRaster = dem
                            slopemax.save('del_maxSl.TIF')
                            arcpy.env.snapRaster = dem
                                    
                            arcpy.MosaicToNewRaster_management("del_minSl.TIF;del_midSl.TIF;del_maxSl.TIF", workspace, "del_cliffProbabilitySlope.TIF", "", "32_BIT_FLOAT", "", "1", "LAST","FIRST")
                            arcpy.env.snapRaster = dem
            
                            # extract cliff probability and apply reduction factor to area outside of buffer.shp
                            if arcpy.management.GetCount("del_lineAndArea_area.shp")[0] == "0":
                                print "del_lineAndArea_area.shp is empty, did not create: CliffProbability_betai" + str("%02d" % (int(minSlope),)) + "betaA"  + str(int(areaSlope))+".TIF"
                            else:  
                                outExtractSlope = ExtractByMask("del_cliffProbabilitySlope.TIF", "del_lineAndArea_area.shp")
                                outExtractSlope.save("del_final_cliffs_found.TIF")
                                
                                arcpy.RasterToFloat_conversion("del_cliffProbabilitySlope.TIF", "del_CliffProbabilitySlope.flt")
                                CliffProbabilitySlope = Raster('del_CliffProbabilitySlope.flt')
                                CliffProbabilitySlopeREDUCED = CliffProbabilitySlope*phi
                                arcpy.env.snapRaster = dem
                                CliffProbabilitySlopeREDUCED.save('del_CliffProbabilitySlopeREDUCED.TIF')
                
                                arcpy.MosaicToNewRaster_management("del_final_cliffs_found.TIF;del_CliffProbabilitySlopeREDUCED.TIF", workspace, "CliffProbability_betai" + str("%02d" % (int(minSlope),)) + "betaA"  + str(int(areaSlope))+".TIF", "", "32_BIT_FLOAT", "", "1", "FIRST","FIRST")
                                arcpy.env.snapRaster = dem
                                
                                del CliffProbabilitySlope
                                del CliffProbabilitySlopeREDUCED
                                                           
                            del minsl
                            del midsl
                            del maxsl


                ## ----------------------------------
                ## Compute percent cliff in total spatial domain

                cliff_area_sum = 0
                debris_area_sum = 0
                Perc_Cliff = 0
                arcpy.CalculateAreas_stats(debarea_iteration, 'del_debris_area.shp')
                with arcpy.da.SearchCursor('del_debris_area.shp', ['F_AREA']) as cursor:
                    for row in cursor:
                        debris_area_sum += row[0]                
                                
                if os.path.isfile(workspace+'\\del_lineAndArea_area.shp') == False:
                    print "'del_lineAndArea_area.shp'does not exist."
                elif arcpy.management.GetCount('del_lineAndArea_area.shp')[0] == "0":
                    print "No area within 'del_lineAndArea_area.shp'."
                else:
                    with arcpy.da.SearchCursor('del_lineAndArea_area.shp', ['F_AREA']) as cursor:
                        for row in cursor:
                            cliff_area_sum += row[0]
                    Perc_Cliff = (cliff_area_sum/debris_area_sum)*100
                    arcpy.Dissolve_management("del_lineAndArea_area.shp", 'cliffMap_betai' + str("%02d" % (int(minSlope),)) + 'betaA' + str(int(areaSlope)) + '.shp', "value")
                    arcpy.AddField_management('cliffMap_betai' + str("%02d" % (int(minSlope),)) + 'betaA' + str(int(areaSlope)) + '.shp','minSlope','FLOAT')
                    arcpy.AddField_management('cliffMap_betai' + str("%02d" % (int(minSlope),)) + 'betaA' + str(int(areaSlope)) + '.shp','Area_Cliff','FLOAT')
                    arcpy.AddField_management('cliffMap_betai' + str("%02d" % (int(minSlope),)) + 'betaA' + str(int(areaSlope)) + '.shp','Area_Deb','FLOAT')
                    
                    arcpy.AddField_management('cliffMap_betai' + str("%02d" % (int(minSlope),)) + 'betaA' + str(int(areaSlope)) + '.shp','Perc_Cliff','FLOAT')
                    rows = arcpy.UpdateCursor('cliffMap_betai' + str("%02d" % (int(minSlope),)) + 'betaA' + str(int(areaSlope)) + '.shp')
                    for row in rows:
                        row.setValue('Area_Cliff', cliff_area_sum)
                        row.setValue('Area_Deb', debris_area_sum)
                        row.setValue('minSlope', minSlope)
                        row.setValue('Perc_Cliff', Perc_Cliff)
                        rows.updateRow(row)
                    del row, rows
                                     
                    print 'IceCliffLocation script [minSlope: ' + str("%02d" % (int(minSlope),)) + ' areaSlope: ' + str(int(areaSlope))+ '] done...'
                                         
        rasterList = arcpy.ListRasters("*del*")
        for raster in rasterList:
            arcpy.Delete_management(raster)
        del raster
        del rasterList

        fcList = arcpy.ListFeatureClasses("*del*")
        for fc in fcList:
            arcpy.Delete_management(fc)
        del fc
        del fcList

        print "intermediate files deleted"
            
    del minSlope
    del n
    
    if str(workspace.split("\\")[-1]) == 'Final':
        print "Script complete"        
    else:
        initialSlope_doubles = []
        percentCliffs_doubles = []
        initialSlope = []
        percentCliffs = []
        xfit = []
        yfit = []
        fcList = []
        arr = []
        fcList = arcpy.ListFeatureClasses("*cliffMap*")
        arcpy.Merge_management(fcList, "mergedSolutions.shp")
        arr = arcpy.da.TableToNumPyArray("mergedSolutions.shp", ('Perc_Cliff','minSlope'))
        arcpy.Delete_management("del_mergedSolutions.shp")
        initialSlope_doubles = [row[1] for row in arr]
        percentCliffs_doubles = [row[0] for row in arr]
        
        #remove rows that are repeated due to (possible) earlier tiled dissolve from insufficient memory 
        for i,j in enumerate(initialSlope_doubles):
            if j != initialSlope_doubles[(i-1) % len(initialSlope_doubles)]:
                initialSlope.append(j)
        del i,j
        for i,j in enumerate(percentCliffs_doubles):
            if j != percentCliffs_doubles[(i-1) % len(percentCliffs_doubles)]:
                percentCliffs.append(j)
        del i,j
                
        def func(x,a,b,c):
            return a*np.exp(-((x-b)/c)**2)
        try:
            popt, pcov = curve_fit(func,initialSlope,percentCliffs, maxfev=1000)
        except RuntimeError:
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            ax1.plot(initialSlope, percentCliffs, 'ko');plt.draw()
            fig.show()            
            print("Error - curve_fit failed")
        xfit = np.linspace(min(initialSlope), max(initialSlope), 100)
        yfit = popt[0]*np.exp(-((xfit-popt[1])/popt[2])**2)
        
        def secondDer(x):
            return popt[0]*(((4*(x-popt[1])**2*np.exp(-(x-popt[1])**2/popt[2]**2))/popt[2]**4)-((2*np.exp(-(x-popt[1])**2/popt[2]**2))/popt[2]**2))
        a1 = []
        a1 = [i for i in xrange(91)]
        a2 = secondDer(a1)
        #the next 3 for loops and a[x] variables define 1 of the 2 points to derive the optimization line.
        a3 = []
        a4 = []
        # values of second derivative where slope is below 'gamma'
        for i, j in enumerate(a2):
            if j <= gamma:
                a3.append(i) == i
        # find the steepest point (in the middle of the side of the bell)
        for i, j in enumerate(a2):
            if j == max(a2):
                m=i
        # take only values to the right of 'm' in case the curve is flat at 0 slope
        for i in a3:
            if i > m:
                a4.append(i) == i
        del i,j
                
        ax = min(a4) 
        ay = popt[0]*np.exp(-((ax-popt[1])/popt[2])**2)
        
        #find max of bell for first point in optmization line
        yfit_array = array(yfit)        
        ftup = (np.where(yfit_array == max(yfit_array)))
        f = int(ftup[0]) # x,y index of max yfit 
                
        # d = distance from fit Equation 2 (Herreid and Pellicciotti, 2018) to line definded by ((xfit[0],yfit[0]),(ax,yx))
        d = abs((yfit[f]-ay)*xfit-(xfit[f]-ax)*yfit+xfit[f]*ay-yfit[f]*ax)/((yfit[f]-ay)**2+(xfit[f]-ax)**2)**(1/2)
        # crit is the index of the longest d
        crit = np.where(d == max(d))
        m = (yfit[f]-ay)/(xfit[f]-ax)
        b = yfit[f]-m*xfit[f]
        x_crit = (xfit[crit]+m*yfit[crit]-m*b)/(m**2+1)
        y_crit = m*((xfit[crit]+m*yfit[crit]-m*b)/(m**2+1))+b
        
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(initialSlope, percentCliffs, 'ko'); plt.plot([xfit[f],ax],[yfit[f],ay]); plt.plot([xfit[crit],x_crit],[yfit[crit],y_crit]); plt.plot(xfit,yfit);plt.xlim(0, 100);plt.ylim(0, 100);plt.gca().set_aspect('equal', adjustable='box');plt.draw()
        ax1.set_xlabel(r'$\mathrm{\beta_i (^\circ)}$')
        ax1.set_ylabel('Ice cliff fraction (%)')
        fig.show()
        plt.waitforbuttonpress()
        
        #save data used to make figure
        np.save(workspace+'\\figureData', (initialSlope, percentCliffs,[xfit[f],ax],[yfit[f],ay],[xfit[crit],x_crit],[yfit[crit],y_crit],xfit,yfit))

        IceCliffLocation.minSlope = float(xfit[crit])

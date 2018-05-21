from __future__ import division
# function called by DebrisCoverTools.py
# By Sam Herreid
#
def DebrisAreaSegmentation(debarea,fishnetRes,lookDistance,workspace):
    import os,arcpy
    from arcpy import env
   
    desc = arcpy.Describe(debarea)
    spatialRef = arcpy.Describe(debarea).spatialReference
    arcpy.CreateFishnet_management("Cliff_"+str(fishnetRes)+"fishnet.shp",str(desc.extent.lowerLeft),str(desc.extent.XMin) + " " + str(desc.extent.YMax + 10),fishnetRes,fishnetRes,"0","0",str(desc.extent.upperRight),"NO_LABELS","#","POLYGON")
    # create 'value' to dissolve further down
    arcpy.AddField_management("Cliff_"+str(fishnetRes)+"fishnet.shp", "value", "SHORT", 1, "", "", "", "", "")
    arcpy.MakeFeatureLayer_management("Cliff_"+str(fishnetRes)+"fishnet.shp", "tempLayer")
    arcpy.SelectLayerByLocation_management("tempLayer", 'WITHIN_A_DISTANCE', debarea,str(-1) + " meters")
    arcpy.SelectLayerByAttribute_management ("tempLayer", "SWITCH_SELECTION")
    arcpy.DeleteFeatures_management("tempLayer")
    arcpy.AddField_management("Cliff_"+str(fishnetRes)+"fishnet.shp",'FIDc','SHORT')
    arcpy.CalculateField_management ("Cliff_"+str(fishnetRes)+"fishnet.shp", "FIDc", "!FID!", "PYTHON_9.3")
    arcpy.DefineProjection_management("Cliff_"+str(fishnetRes)+"fishnet.shp", spatialRef)
    arcpy.Intersect_analysis (["Cliff_"+str(fishnetRes)+"fishnet.shp",debarea], "tiles.shp", "ALL", "", "")
    arcpy.AddField_management('tiles.shp','Perc_gl','FLOAT')
    
    rows = arcpy.UpdateCursor("tiles.shp")
    for row in rows:
         row.Perc_gl = (row.shape.area/fishnetRes**2)*100
         rows.updateRow(row) 
    del row, rows
    arcpy.JoinField_management("Cliff_"+str(fishnetRes)+"fishnet.shp", "FIDc", "tiles.shp", "FIDc", ["Perc_gl"])
    
    counter = 0
    while True:
        if arcpy.management.GetCount("Cliff_"+str(fishnetRes)+"fishnet.shp")[0] == "0":
            break
        else:
            n = []  
            rows = arcpy.SearchCursor("Cliff_"+str(fishnetRes)+"fishnet.shp")  
            for row in rows:  
                n.append(row.getValue("FIDc"))  
            del row, rows         
            n.sort() 
            arcpy.SelectLayerByAttribute_management("tempLayer", "CLEAR_SELECTION")
            noSelection = []
            noSelection = int(str(arcpy.GetCount_management("tempLayer")))
            arcpy.SelectLayerByAttribute_management("tempLayer", "NEW_SELECTION", "FIDc="+ str(n[0]))
            arcpy.SelectLayerByLocation_management("tempLayer", "SHARE_A_LINE_SEGMENT_WITH","tempLayer", "", "NEW_SELECTION")
            arcpy.SelectLayerByAttribute_management("tempLayer", "REMOVE_FROM_SELECTION", "FIDc="+ str(n[0]))
            result = []
            result = arcpy.GetCount_management("tempLayer")
            if int(result.getOutput(0)) == noSelection:
                #condition where no tiles share a line segment
                arcpy.SelectLayerByAttribute_management("tempLayer", "NEW_SELECTION", "FIDc="+ str(n[0]))
                arcpy.SelectLayerByLocation_management("tempLayer","WITHIN_A_DISTANCE","tempLayer", str(fishnetRes*lookDistance) + " meters", "NEW_SELECTION") 
                arcpy.SelectLayerByAttribute_management("tempLayer", "REMOVE_FROM_SELECTION", "FIDc="+ str(n[0]))
                #if still no shapes after look distance
                result = arcpy.GetCount_management("tempLayer")
                if int(result.getOutput(0)) == 0:
                    arcpy.CreateFeatureclass_management(workspace, "Cliff_"+str(fishnetRes)+"fishnet_iteration.shp", "POLYGON","tempLayer")
                else:
                    arcpy.CopyFeatures_management("tempLayer", "Cliff_"+str(fishnetRes)+"fishnet_iteration.shp")
            
            else:
                arcpy.CopyFeatures_management("tempLayer", "Cliff_"+str(fishnetRes)+"fishnet_iteration.shp")
    
            # populate listFIDc: unique ID of 'share a boundary' shapes in "Cliff_"+str(fishnetRes)+"fishnet_iteration.shp" 
            listFIDc = []
            tiles = arcpy.SearchCursor("Cliff_"+str(fishnetRes)+"fishnet_iteration.shp")        
            for tile in tiles:
                flag = True
                b = tile.getValue("FIDc")
                listFIDc.append(b)
            if not flag:
                listFIDc = []                      
            # iterate through features in "Cliff_"+str(fishnetRes)+"fishnet_iteration.shp" and find one (if exists) with a summed area below fishnetRes^2
            tileNumber = len(listFIDc)
            tileCount = 0
            summation = 101
            breakTracker = []
            while summation > 100:
                print str(tileCount)+" of "+str(tileNumber)+"   (tileCount of tileNumber)"
                arcpy.SelectLayerByAttribute_management("tempLayer", "CLEAR_SELECTION")
                if tileCount == tileNumber:
                    if os.path.exists(workspace+"DebrisCutForCliffs"+str(counter)+".shp"):
                        arcpy.Delete_management(workspace+"DebrisCutForCliffs"+str(counter)+".shp")
                        arcpy.RefreshCatalog(workspace)
                        pathFinal = workspace+"DebrisCutForCliffs"+str(counter)+".shp"
                    else:
                        pathFinal = workspace+"DebrisCutForCliffs"+str(counter)+".shp"
                    # extract deb area
                    arcpy.SelectLayerByAttribute_management("tempLayer", "NEW_SELECTION", "FIDc="+ str(n[0]))
                    arcpy.Intersect_analysis (["tempLayer", debarea], pathFinal)
                    arcpy.DeleteFeatures_management("tempLayer")
                    arcpy.Delete_management("Cliff_"+str(fishnetRes)+"fishnet_iteration.shp")
                    counter = counter+1
                    print "Counter updated: "+str(counter)
                    breakTracker = 1
                    break                     
                else:
                    arcpy.SelectLayerByAttribute_management("tempLayer", "NEW_SELECTION", "FIDc="+ str(n[0]))
                    arcpy.SelectLayerByAttribute_management("tempLayer", "ADD_TO_SELECTION", "FIDc="+ str(listFIDc[tileCount]))
                    areaList = []
                    rows = arcpy.SearchCursor("tempLayer")  
                    for row in rows:  
                        s = row.getValue("Perc_gl")
                        areaList.append(s)
                    del row, rows
                    print "areaList:"
                    print(areaList)
                    summation = sum(areaList)
                    print "summation: "+str(summation)
                    #if summation <= 100:
                    #    break
                    #else:
                    tileCount = tileCount+1
                    print "tileCount "+str(tileCount-1) +" updated to "+str(tileCount)
                    continue
                    
            if breakTracker == 1:
                breakTracker = []
                continue
            else:
                if not os.path.exists(workspace+"DebrisCutForCliffs0.shp"):
                    pathDissolve = workspace+"DebrisDissolveForCliffs0.shp"
                    pathFinal = workspace+"DebrisCutForCliffs0.shp"
                else:
                    fcListFinal = arcpy.ListFeatureClasses("*DebrisCutForCliffs*")
                    fcListFinal.sort()
                    s = fcListFinal[::-1][0]
                    if counter - int(s.split("Cliffs",1)[1].split(".shp")[0]) == 0:
                        arcpy.Delete_management(workspace+"DebrisCutForCliffs"+str(counter)+".shp")
                        arcpy.Delete_management(workspace+"DebrisDissolveForCliffs"+str(counter)+".shp")
                        arcpy.RefreshCatalog(workspace)
                        pathDissolve = workspace+"DebrisDissolveForCliffs"+str(counter)+".shp"
                        pathFinal = workspace+"DebrisCutForCliffs"+str(counter)+".shp"
                    else:
                        pathDissolve = workspace+"DebrisDissolveForCliffs"+str(counter)+".shp"
                        pathFinal = workspace+"DebrisCutForCliffs"+str(counter)+".shp"
    
                # merge two tiles
                arcpy.Dissolve_management("tempLayer", pathDissolve,"value")
                # extract deb area              
                arcpy.Intersect_analysis ([pathDissolve, debarea], pathFinal) 
                # update Perc_gl             
                fields = ['Perc_gl']
                fieldList = arcpy.ListFields(pathDissolve)    
                fieldName = [f.name for f in fieldList]
                for field in fields:
                    if field in fieldName:
                        print "Field 'Perc_gl' already exists, not replaced"
                    else:
                        arcpy.AddField_management(pathDissolve, field, 'FLOAT')
                del field, fields
                del f, fieldList
                del fieldName
                # update FIDc
                rows = arcpy.UpdateCursor(pathDissolve)
                for row in rows:
                    row.Perc_gl = summation
                    rows.updateRow(row) 
                del row, rows
                fields = ['FIDc']
                fieldList = arcpy.ListFields(pathDissolve)    
                fieldName = [f.name for f in fieldList]
                for field in fields:
                    if field in fieldName:
                        print "Field 'FIDc' already exists, not replaced"
                    else:
                        arcpy.AddField_management(pathDissolve, field,'SHORT')
                del field, fields
                del f, fieldList
                del fieldName
                features = arcpy.UpdateCursor(pathDissolve)
                for feature in features:
                    feature.FIDc = counter
                    features.updateRow(feature)
                del feature,features
    
                arcpy.MakeFeatureLayer_management(pathDissolve, "tempLayer1")
                arcpy.SelectLayerByAttribute_management("tempLayer", "CLEAR_SELECTION")
                arcpy.Update_analysis("tempLayer","tempLayer1", "update.shp")
                arcpy.Delete_management("Cliff_"+str(fishnetRes)+"fishnet.shp")
                arcpy.RefreshCatalog(workspace)
                arcpy.Rename_management("update.shp","Cliff_"+str(fishnetRes)+"fishnet.shp")
                arcpy.RefreshCatalog(workspace)
                arcpy.MakeFeatureLayer_management("Cliff_"+str(fishnetRes)+"fishnet.shp", "tempLayer")
                #Delete last feature to exit while loop
                if arcpy.management.GetCount("Cliff_"+str(fishnetRes)+"fishnet.shp")[0] == "1":
                    arcpy.MakeFeatureLayer_management("Cliff_"+str(fishnetRes)+"fishnet.shp", "tempLayer2")
                    arcpy.SelectLayerByLocation_management("tempLayer2", 'WITHIN_A_DISTANCE', workspace+"\\DebrisCutForCliffs"+str(counter)+".shp",str(-1) + " meters")
                    arcpy.DeleteFeatures_management("tempLayer2")
                    arcpy.Delete_management(pathDissolve)
                    arcpy.Delete_management("tempLayer1")
                    arcpy.Delete_management("Cliff_"+str(fishnetRes)+"fishnet_iteration.shp")
                    print "tile "+str(counter)+" assigned"
                    continue
                else:
                    arcpy.Delete_management(pathDissolve)
                    arcpy.Delete_management("tempLayer1")
                    arcpy.Delete_management("Cliff_"+str(fishnetRes)+"fishnet_iteration.shp")
                    print "tile "+str(counter)+" assigned"
                    continue
                
    arcpy.Delete_management("tempLayer")
    arcpy.Delete_management("tiles.shp")
    arcpy.Delete_management("Cliff_"+str(fishnetRes)+"fishnet.shp")

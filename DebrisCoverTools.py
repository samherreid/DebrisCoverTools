##
## Debris Cover Tools 
## Version 1.0
##
## By Sam Herreid (samherreid@gmail.com)
## 
## A suite of automated tools to:
##      Map supraglacial debris cover (DebisMap.py)
##      Locate ice cliffs (DebrisAreaSegmentation.py, IceCliffLocation.py)
##      Locate supraglacial lakes/ponds [in prep., not in v1.0]
##      Measure changes in debris cover [in prep., not in v1.0]
##      Calculate debris map and area change omission and commission errors [in prep., not in v1.0]
##      Identify glacier flow instabilities (optional: in near real time) [in prep., not in v1.0]
##      
## For use of Debris Cover Tools v1.0, required input data are:
##      Glacier outline(s) (.shp)
##      Landsat TM, ETM+, or OLI images (.tif, do not change default file names)
##      Digital Elevation Model roughly coincident in time with Landsat imagery (.tif, aprox. 5m resolution)
##
## Required software are:
##      ArcGIS/arcpy (advanced licence, proprietary)
##      Python (2.x to be compatible with arcpy)
##      numpy (Python package)
##      scipy (Python package)
##      matplotlib (Python package)
##
## Please cite the following article(s) if using this code to
## 
## map ice cliffs:
##      Herreid, Sam, and Francesca Pellicciotti. "Automated detection of ice cliffs within supraglacial debris cover." The Cryosphere, 2018.
##
## derive debris area changes [code in prep., not in v1.0]:
##      Herreid, Sam, et al. "Satellite observations show no net change in the percentage of supraglacial debris-covered area in northern Pakistan from 1977 to 2014." Journal of Glaciology 61.227 (2015): 524-536.
##
## detect glacier flow instabilities [code in prep., not in v1.0]:
##      Herreid, Sam, and Martin Truffer. "Automated detection of unstable glacier flow and a spectrum of speedup behavior in the Alaska Range." Journal of Geophysical Research: Earth Surface 121.1 (2016): 64-81.
##
##--------------------------------------------------------------------------------------------------------------------------------
##
## To use Debris Cover Tools, follow the directions in comments and boxes like this:
###-------------------------------------------###
###                Directions                 ###
###-------------------------------------------###            

##--------------------------------------------------------------------------------------------------------------------------------

###-------------------------------------------###
###             What do you want?             ###
###-------------------------------------------###

Want_DebrisMap = 'True'                  # DEFINE: workspace, data_dir, shp_dir, mask_dir (mask_dir currently does nothing in v1.0) 
Want_CloudRemoval = 'False'              # in prep., not in v1.0, 'True' will not currently work 
Want_SupraglacialPondLocation = 'False'  # in prep., not in v1.0, 'True' will not currently work 
Want_IceCliff = 'True'                   # DEFINE: workspace, data_dir, shp_dir and dem (that is relatively coincident in time with Landsat (ETM+ or OLI) image). if Want_DebrisMap = 'False', also define: debarea;    
Want_dDebris = 'False'                   # in prep., not in v1.0, 'True' will not currently work
Want_LocateUnstableFlow = 'False'        # in prep., not in v1.0, 'True' will not currently work

###-------------------------------------------###
###          Define directories here:         ###
###-------------------------------------------###

# Example format for directories: "C:\\Users\\Sam\\Desktop\\CanwellGlacier\\" or r"C:\Users\Sam\Desktop\CanwellGlacier\" or "C:/Users/Sam/Desktop/CanwellGlacier/"
# Replace the example paths below to your local data. Note "\\" at end.

workspace = "C:\\Users\\Sam\\Desktop\\CanwellGlacier\\" # Existing location where new files will be created

data_dir = "C:\\Users\\Sam\\Desktop\\Landsat\\" # Location of uncompressed landsat images. Do not change NASA file names.

shp_dir  = "C:\\Users\\Sam\\Desktop\\Glacier\\" # Location of glacier outlines as shapefiles

mask_dir = "" # Location of cloud and error masks [in prep., not in v1.0]

dem = "C:\\Users\\Sam\\Desktop\\dem\\CanwellGlacier_072016.tif" # Location of DEM. NOTICE: rename the .tif file such that the ending is _mmyyyy.tif where mmyyyy = the month and year of DEM data aquisition

debarea = "" # Location of debris map .shp, only requred if Want_DebrisMap = 'False'

###-------------------------------------------###
###         Define parameters here:           ###
###-------------------------------------------###

##----------------------------------------------
## DebrisMap:
##----------------------------------------------

A_remove = 2700             # Area (m2) to be filtered out of result
A_fill = 2700               # Area (m2) to be filled and considered debris cover
landsat = 8                 # Number of data acquiring Landsat satellite number. Accepted valueds are 5,7 or 8

                            # Threshold values from Herreid et al., 2015. Go into DebisMap.py to change these values 
                            # File name convention: (glacier name)_---y(year)---d(day of year)_---t(integer threshold *100)----r(area removed in m2)----f(area filled in m2)
                            # e.g.: CanwellGlacier_2015y249d_145t2700r2700f

##----------------------------------------------
## DebrisAreaSegmentation:
##----------------------------------------------

L_t = 1500                  # Edge length (meters) of approximate square area for which cliffs will be solved for. This might be necessary due to memory limitations in ArcGIS
n_c = 1                     # Coefficient to L_t (fishnetRes) that will look for tiles to merge area with if none share a boundary

##----------------------------------------------
## IceCliffLocation:
##----------------------------------------------

pixel = 'auto'              # If 'auto': working and final resolution is set to DEM resolution. If not 'auto' define an integer spatial resolution (m) outside of quotes
n_iterations = 36           # Number of iterations; fewer for faster computation 
L_e = 10                    # m on ice cliff ends 
alpha = 2                   # Centerline buffer distance (n_pixels*root2 over 2) 
beta_e = 3                  # Degrees by which beta*_i is reduced to define {A_e}_i (see Herreid and Pellicciotti, 2018)
A_min = 10                  # Minimum ice cliff area threshold in n pixels 
phi = 0.5                   # Ice cliff probability, p(x=ice cliff given surface slope and omega), not affirmed by the code will be multiplied (reduced) by this factor (omega defined in Herreid and Pellicciotti, 2018)
gamma = 0.0001              # Tolerance to asymptote, defines line used to find optimized value
                            # File name convention: mmyyyy(demDate)_beta_e-(beta_e)_alpha--(10*alpha)_lineExt--(L_e)m_minPixs--(A_min)_res-(pixel)m
                            # e.g.: 072016_beta_e3_alpha20_lineExt10m_minPixs10_res5m

###-------------------------------------------###
###  Should not need to edit below this box!  ###
###-------------------------------------------###

import sys,os,arcpy
from arcpy import env
env.overwriteOutput = True

demDate = dem.split("\\")[-1].split("_")[1].split(".")[0]
if len(dem.split("\\")[-1].split("_")[1].split(".")[0]) != 6:
    print "DEM path suffix not in the format: _mmyyyy.tif where mmyyyy = the month and year of DEM data aquisition."
    sys.exit()
if pixel == 'auto':
    pixel = int(round(float(str(arcpy.GetRasterProperties_management(dem, "CELLSIZEX")))))
    print "Resolution set to: "+str(pixel)+"m"
workspaceSplit = workspace.split("\\")[-1]
workspace = workspace[:-workspaceSplit.count('')]+'\\'
workspace = workspace+str(demDate)+'_beta_e'+str(int(beta_e))+'_alpha'+str(int(10*alpha))+'_lineExt'+str(int(L_e))+'m_minPixs'+str(int(A_min))+'_res'+str(int(pixel))+'m\\'
try:
    os.makedirs(workspace)
    env.workspace = workspace
    Want_CliffProcessingSegments = 'True'
except:
    print "Parent workspace already exist, skipping straight to see if there are missing ice cliff iterations..."
    print "If you changed the number of iterations, missing iterations will be incorrectly identified!"
    Want_DebrisMap = 'False'
    Want_CliffProcessingSegments = 'False'

##---------------------------------------------------  DebrisMap  --------------------------------------------------

if Want_DebrisMap == 'True':   
    workspace = workspace+'DebrisMap\\'
    try:
        os.makedirs(workspace)
        env.workspace = workspace
    except:
        print "Debris map workspace cannot be created. It may already exist."
        sys.exit()
      
    if Want_CloudRemoval != 'True':
        mask_dir = os.makedirs(workspace+'empty')
    import DebrisMap
    DebrisMap.DebrisMap(workspace,data_dir,landsat,shp_dir,mask_dir,A_remove,A_fill,Want_CloudRemoval)
    finddeb = arcpy.ListFeatureClasses('*MERGED*')
    debarea = workspace+finddeb[0]
    del finddeb
    if Want_CloudRemoval != 'True':
        del mask_dir
        arcpy.Delete_management(workspace+'empty')
else:
    workspace = workspace+'DebrisMap\\'   

##-----------------------------------------  CliffProcessingSegments  ------------------------------------------------

if Want_CliffProcessingSegments == 'False':
    workspaceSplit = workspace.split("\\")[-2]
    workspace = workspace[:-workspaceSplit.count('')]
    workspace = workspace+'CliffProcessingSegments\\'
else:
    arcpy.CalculateAreas_stats(debarea, 'debareaMeters.shp')
    rows = arcpy.SearchCursor('debareaMeters.shp')  
    for row in rows:  
        debarea_m2 = row.getValue("F_AREA")
    del row, rows
    arcpy.Delete_management('debareaMeters.shp')
    workspaceSplit = workspace.split("\\")[-2]
    workspace = workspace[:-workspaceSplit.count('')]
    workspace = workspace+'CliffProcessingSegments\\'
    fishnetRes = L_t #name follows Herreid and Pellicciotti, 2018
    lookDistance = n_c #name follows Herreid and Pellicciotti, 2018
    try:
        os.makedirs(workspace)
        env.workspace = workspace
    except:
        print "Cliff segmentation workspace cannot be created. It may already exist."
        sys.exit()
    if debarea_m2 <= fishnetRes**2:
        print "Debris covered area is "+str(debarea_m2)+"m2, less than fisnetRes^2: "+str(fishnetRes**2)+" m2. Cliff area will be solved for without breaking into tiles."
        arcpy.CopyFeatures_management(debarea,"DebrisCutForCliffs0.shp")
    else:
        import DebrisAreaSegmentation 
        DebrisAreaSegmentation.DebrisAreaSegmentation(debarea,fishnetRes,lookDistance,workspace)
    
##-------------------------------------------  IceCliffLocation  ----------------------------------------------------   
workspaceSegmentation = workspace
workspaceSplit = workspace.split("\\")[-2]
workspace = workspace[:-workspaceSplit.count('')]
workspace = workspace+'IceCliffs'
env.workspace = workspace


tilelist = []    
dirlist=os.listdir(workspaceSegmentation)
for item in dirlist:
    if item.lower().endswith(".shp"):
        tilelist.append(item)
del item, dirlist
print "Tile list for cliff code:"
print tilelist
for tile in tilelist:
    tileDebarea = workspaceSegmentation+tile    
    workspace = workspace+'\\'+tile.split(".")[0]
    try:
        os.makedirs(workspace)
        env.workspace = workspace
    except:
        print "Ice cliff workspace exists, will try to finish missing iterations..."
        env.workspace = workspace
        
    minSlope = []
    import IceCliffLocation
    IceCliffLocation.IceCliffLocation(workspace,dem,tileDebarea,pixel,minSlope,n_iterations,L_e,alpha,beta_e,A_min,phi,gamma)
    
    #define optimized minSlope
    minSlope = IceCliffLocation.IceCliffLocation.minSlope 
    workspace = workspace+'\\Final'
    try:
        os.makedirs(workspace)
        env.workspace = workspace
    except:
        print "Final workspace cannot be created. It may already exist."
        sys.exit()
        
    IceCliffLocation.IceCliffLocation(workspace,dem,tileDebarea,pixel,minSlope,n_iterations,L_e,alpha,beta_e,A_min,phi,gamma)
    # remove 'final'    
    workspaceSplit = workspace.split("\\")[-1]
    workspace = workspace[:-workspaceSplit.count('')]
    # remove completed tile file  
    workspaceSplit = workspace.split("\\")[-1]
    workspace = workspace[:-workspaceSplit.count('')]
del tile, tilelist
del workspaceSegmentation

#merge final cliff map
dirfinals = []
for file in os.listdir(workspace):
    if file.startswith("DebrisCutForCliffs"):
        dirfinals.append(workspace+ '\\'+ file +'\\Final')
finalShape = []
finalProb = []
for dirfinal in dirfinals:
    for subfile in os.listdir(dirfinal):
        if subfile.startswith('cliffMap') and subfile.lower().endswith('shp'):
            finalShape.append(dirfinal+'\\'+subfile)
        elif subfile.startswith('CliffProbability') and subfile.lower().endswith('tif'):
            finalProb.append(dirfinal+'\\'+subfile)
workspace = workspace + '\\CliffMap_finalMerged'
try:
    os.makedirs(workspace)
    env.workspace = workspace
except:
    print "Final workspace cannot be created. It may already exist."
    sys.exit()
arcpy.Merge_management(finalShape, workspace+'\\merged.shp')
arcpy.Dissolve_management(workspace+'\\merged.shp', workspace+'\\CliffMap_merged.shp')
arcpy.Delete_management(workspace+'\\merged.shp')
arcpy.MosaicToNewRaster_management(finalProb, workspace,"CliffProbabilityMap_merged.tif", "","32_BIT_FLOAT", "", "1")

import os
from tqdm import tqdm

faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
outputDir = "/home/student/Documents/FYP3164/Hamza/dataset"
imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs"

def extractPose(filename):
    
    os.system(f"./FaceLandmarkImg -f {imgDir}/{filename} -out_dir {outputDir}/pose -pose")

def extractAus(filename):
    
    os.system(f"./FaceLandmarkImg -f {imgDir}/{filename} -out_dir {outputDir}/aus -aus")

def setGlobals(landmarkDir, outDir, imgdir):
    global faceLandmarkDir,outputDir, imgDir
    flag = True
    if os.path.isdir(landmarkDir):
        faceLandmarkDir = landmarkDir 
        os.chdir(faceLandmarkDir)
    else:
        flag = False
    if os.path.isdir(outDir):
        outputDir = outDir
    else:
        os.makedirs(outDir)
    if os.path.isdir(imgdir):
        imgDir = imgdir
    else:
        flag = False
    return flag


def main():
    
    setGlobals( "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin", "/home/student/Documents/FYP3164/Hamza/dataset",  "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs" )

    for file in tqdm(os.listdir(imgDir)):
        extractPose(file)
        extractAus(file)

    

if __name__ == '__main__':
    main()
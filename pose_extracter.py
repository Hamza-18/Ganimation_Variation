import imghdr
import os
from tqdm import tqdm

faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
outputDir = "/home/student/Documents/FYP3164/Hamza/dataset"
imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs"

def extractPose(filename):
    
    os.system(f"./FaceLandmarkImg -f {imgDir}/{filename} -out_dir {outputDir} -pose")

def main():
    os.chdir(faceLandmarkDir)
    for file in tqdm(os.listdir(imgDir)):
        extractPose(file)

    

if __name__ == '__main__':
    main()
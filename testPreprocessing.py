import unittest
from pose_aus_extracter import setGlobals, extractPose, extractAus
import os

class Test(unittest.TestCase):

    def test_extractPose(self):
        pass

    def test_global_parameters(self):
        """correct directories are given"""
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
        outputDir = "/home/student/Documents/FYP3164/Hamza/dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs"
        self.assertTrue(setGlobals(faceLandmarkDir, outputDir, imgDir), "wrong directories provided")
        self.assertEqual(os.getcwd(),faceLandmarkDir)

    def test_global_parameters_two(self):
        """"Wrong directories provided"""
        os.chdir("/home/student/Desktop")
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin1"
        outputDir = "/home/student/Documents/FYP3164/Hamza/dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs"
        self.assertFalse(setGlobals(faceLandmarkDir, outputDir, imgDir))
        self.assertNotEqual(os.getcwd, faceLandmarkDir)

        os.chdir("/home/student/Desktop")
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
        outputDir = "/home/student/Documents/FYP3164/Hamza/dataset/2"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs"
        self.assertTrue(setGlobals(faceLandmarkDir, outputDir, imgDir))
        self.assertTrue(os.path.isdir(outputDir))

        os.chdir("/home/student/Desktop")
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin1"
        outputDir = "/home/student/Documents/FYP3164/Hamza/dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celebA/imgs/2"
        self.assertFalse(setGlobals(faceLandmarkDir, outputDir, imgDir))
        self.assertNotEqual(os.getcwd(), faceLandmarkDir)
    
    def test_pose_exractor(self):
        """check pose features are extracted"""
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
        outputDir = "/home/student/Documents/FYP3164/Hamza/test_dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celeba/imgs"
        setGlobals(faceLandmarkDir, outputDir, imgDir)
        extractPose("000077.jpg")
        self.assertTrue(os.path.isfile(outputDir+"/pose/000077.csv"))

    def test_pose_exractor_two(self):
        """check wrong file name is handled"""
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
        outputDir = "/home/student/Documents/FYP3164/Hamza/test_dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celeba/imgs"
        setGlobals(faceLandmarkDir, outputDir, imgDir)
        extractPose("00007.jpg")
        self.assertFalse(os.path.isfile(outputDir+"/pose/00007.csv"))

    def test_aus_exractor(self):
        """check if action units are extracted"""
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
        outputDir = "/home/student/Documents/FYP3164/Hamza/test_dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celeba/imgs"
        setGlobals(faceLandmarkDir, outputDir, imgDir)
        extractAus("00007.jpg")
        self.assertFalse(os.path.isfile(outputDir+"/aus/00007.csv"))

    def test_aus_exractor_two(self):
        """check if wrong file name is handled"""
        faceLandmarkDir = "/home/student/Documents/FYP3164/Hamza/OpenFace-master/build/bin"
        outputDir = "/home/student/Documents/FYP3164/Hamza/test_dataset"
        imgDir = "/home/student/Documents/FYP3164/Hamza/ganimation_variation/celeba/imgs"
        setGlobals(faceLandmarkDir, outputDir, imgDir)
        extractAus("000077.jpg")
        self.assertTrue(os.path.isfile(outputDir+"/aus/000077.csv"))
    
    def test_pose_annotatons(self):
        """check pkl file generated for pose"""
        os.system("python /home/student/Documents/FYP3164/Hamza/Ganimation_Variation/pose_annotation.py -ia /home/student/Documents/FYP3164/Hamza/test_dataset/pose -op /home/student/Documents/FYP3164/Hamza/test_dataset/result" )
        self.assertTrue(os.path.isfile("/home/student/Documents/FYP3164/Hamza/test_dataset/result/pose_aus.pkl"))

    def test_pose_annotatons(self):
        """check pkl file generated for action units"""
        os.system("python /home/student/Documents/FYP3164/Hamza/Ganimation_Variation/data_annotations.py -ia /home/student/Documents/FYP3164/Hamza/test_dataset/pose -op /home/student/Documents/FYP3164/Hamza/test_dataset/result" )
        self.assertTrue(os.path.isfile("/home/student/Documents/FYP3164/Hamza/test_dataset/result/aus_openface.pkl"))



if __name__ == "__main__":
    unittest.main()
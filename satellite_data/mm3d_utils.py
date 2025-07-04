import numpy as np
from numpy import array
import matplotlib.pyplot as plt 
import cv2
import io
import struct

def plot_images(aIs):
  fig, ax = plt.subplots(1,len(aIs),figsize=[15, 15])

  if len(aIs)==1 :
    ax = [ax]

  for i in range(len(aIs)) :
    ax[i].imshow(aIs[i],cmap='gray') 
    ax[i].get_yaxis().set_ticks([])
    ax[i].get_xaxis().set_ticks([])
    ax[i].set_axis_off()

def plot_DoD(aIs):
  fig, ax = plt.subplots(1,len(aIs),figsize=[15, 15])

  if len(aIs)==1 :
    ax = [ax]

  for i in range(len(aIs)) :
    ax[i].imshow(aIs[i],cmap=plt.get_cmap('RdYlBu'))
    ax[i].get_yaxis().set_ticks([])
    ax[i].get_xaxis().set_ticks([])
    ax[i].set_axis_off()

def plot_tiepts(aTPts,color='lime') :
  axes = plt.gcf().axes

  Nb = len(aTPts)

  for i in range(Nb) :
      axes[i].scatter(aTPts[i][:,0], aTPts[i][:,1], c=color, linewidths=0) 

def plot_tiepts2(aTPts,color='lime') :
  axes = plt.gcf().axes
  NbAxes = len(axes)

  if NbAxes == 2 :
    axes[0].scatter(aTPts[:,0,0], aTPts[:,0,1], c=color, linewidths=0) 
    axes[1].scatter(aTPts[:,1,0], aTPts[:,1,1], c=color, linewidths=0)    
  else :
    axes[0].scatter(aTPts[:,0,0], aTPts[:,0,1], c=color, linewidths=0) 

def TabToMatrix(TabMat) :
    a,b,c,d,e,f,g,h = TabMat
    return array([[a,b,c],[d,e,f],[g,h,1.0]])



# ===== Transforme un fichier texte de point homologue en un tableau [  ... [[x1 y1] [ x2 y2]] ....] 
def ImportHom(NameFile) :
    File=open(NameFile,'r')
    Result = []
    for LStr in File.readlines() :
        aLFloat = []
        for x in  LStr.split(" ") :
           aLFloat.append(float(x))
        x1,y1,x2,y2 = aLFloat[0:4]
        Result.append([[x1,y1],[x2,y2]])
    File.close()
    return Result

def GetIntensity(Points,Im1,Im2):
    print("ddd ",np.shape(Points))
    Intensities = []
    for Pt1,Pt2 in Points :
        x,y = Pt1

        x = int(np.floor(x))
        y = int(np.floor(y))
       
        #print(x,y)
        aInt = Im1[y][x]
        Intensities.append([aInt,aInt,aInt])

    return Intensities


def SaveToPly(FileName,Points3D,RGBVal=[]):

    IsRGB=False
    if len(RGBVal):
        IsRGB = True

    NbPts = len(Points3D)

    FOut = open(FileName,'wb')

    FOut.write(bytes('ply\n', 'utf-8'))
    FOut.write(bytes('format binary_little_endian 1.0\n', 'utf-8'))
    FOut.write(bytes('element vertex %d\n'%NbPts, 'utf-8'))
    FOut.write(bytes('property float x\n', 'utf-8'))
    FOut.write(bytes('property float y\n', 'utf-8'))
    FOut.write(bytes('property float z\n', 'utf-8')) 
    if IsRGB == True:
        FOut.write(bytes('property uchar red\n', 'utf-8'))
        FOut.write(bytes('property uchar green\n', 'utf-8'))
        FOut.write(bytes('property uchar blue\n', 'utf-8'))  
    FOut.write(bytes('end_header\n', 'utf-8'))
 
    if IsRGB == False:
        for X,Y,Z in Points3D: 
            FOut.write(bytearray(struct.pack("fff",X,Y,Z)))
    else :
        for XYZ,RGB in zip(Points3D,RGBVal):   
            FOut.write(bytearray(struct.pack("fffccc",
                                         XYZ[0],XYZ[1],XYZ[2], 
                                         RGB[0].tostring(),RGB[1].tostring(),RGB[2].tostring())))


    FOut.close()





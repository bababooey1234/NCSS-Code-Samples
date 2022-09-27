# apparently this was created before I knew what comments were.
# needs OBS installed to use its virtual camera, plus a couple libraries.
# takes a frame from the laptop camera, finds the hands in that frame, draw the hand skeletons,
# if plus is pressed draws a circle at each fingertip, and pushes frame to OBS virtual camera to be displayed in zoom/teams.
# example frame in zoomCameraExample.png
import cv2
import mediapipe as mp
import win32api,win32con
from datetime import datetime as dt
import pyvirtualcam
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
drawing_styles = mp.solutions.drawing_styles
lastpress=dt.now()
lastCamPress=dt.now()
lastReset=dt.now()
lastAdd=dt.now()
activateEffects=False
activateCam=True
actionList=[]

def new_webcam():
    cam=cv2.VideoCapture(0)
    cam.set(3,1280)
    cam.set(4,720)
    return cam

cap=new_webcam()
    
def check_reset():
    global lastReset
    if win32api.GetAsyncKeyState(win32con.VK_SUBTRACT):
        if (dt.now()-lastReset).seconds>1:
            print("- pressed")
            lastReset=dt.now()
            return True
    return False

def check_add():
    global lastAdd
    if win32api.GetAsyncKeyState(win32con.VK_ADD):
        print("+ pressed")
        return True
        """
        if (dt.now()-lastAdd).microseconds>500000:
            print("+ pressed")
            lastAdd=dt.now()
            return True
        """
    return False

def check_toggleEffects():
    global lastpress
    global activateEffects
    if win32api.GetAsyncKeyState(win32con.VK_MULTIPLY):
        if (dt.now()-lastpress).seconds>2:
            print("* pressed")
            lastpress=dt.now()
            activateEffects=not activateEffects

def check_toggleCam():
    global lastCamPress
    global activateCam
    global cap
    if win32api.GetAsyncKeyState(win32con.VK_DIVIDE):
        if (dt.now()-lastCamPress).seconds>2:
            print("/ pressed ")
            lastCamPress=dt.now()
            activateCam=not activateCam
            if not activateCam:
                cap.release()
                cap=None
            else:
                cap=new_webcam()

def check_keys(queue):
    global actionList
    #reset always takes priority
    if(check_reset()):
        actionList=[]
        #reset overlay
    elif(check_add()):
        for point in queue:
            actionList.append(point)
            print(f"point {point} added")
        #add point
        

# For webcam input:
try:
    with pyvirtualcam.Camera(width=1280, height=720, fps=30, fmt=pyvirtualcam.PixelFormat.BGR) as cam:
        with mp_hands.Hands(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as hands:
          print("starting")
          print("numpad / to start camera, * to toggle effects, + to add line, - to remove.")
          while True:
            check_toggleCam()
            check_toggleEffects()
            if not activateCam:
                image=np.zeros((720,1280,3),np.uint8)
                cam.send(image)
                continue
            success, image = cap.read()
            if not success:
              print("Ignoring empty camera frame.")
              # If loading a video, use 'break' instead of 'continue'.
              continue

            if activateEffects:
              # Flip the image horizontally for a later selfie-view display, and convert
              # the BGR image to RGB.
              #image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
              #edit: removed flipping
              image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
              # To improve performance, optionally mark the image as not writeable to
              # pass by reference.
              
              image.flags.writeable = False
              results = hands.process(image)

              # Draw the hand annotations on the image.
              image.flags.writeable = True
              image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
              queue=[]
              if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                  mp_drawing.draw_landmarks(
                      image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                      drawing_styles.get_default_hand_landmarks_style(),
                      drawing_styles.get_default_hand_connections_style())
                  normalizedLandmark = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                  queue.append(mp_drawing._normalized_to_pixel_coordinates(normalizedLandmark.x, normalizedLandmark.y, 1280, 720))
              check_keys(queue)
            else:
              if check_reset():
                  actionList=[]
            for point in actionList:
              image=cv2.circle(image,point,9,(0,0,255),-1)
              #for i in range(0,len(actionList)-1,2):
                  #image=cv2.line(image,actionList[i],actionList[i+1],(0,0,255),10)
            
            cam.send(image)
            #cv2.imshow('MediaPipe Hands', image)
            #cv2.waitKey(1)
            #cam.sleep_until_next_frame()
            #cam.sleep_until_next_frame()
finally:
    if cap is not None:
            cap.release()

import mediapipe as mp
import cv2
import socket
import random
import math
import numpy as np
from google.protobuf.json_format import MessageToDict
import tkinter as tk
import socket
import tkinter.font

server_ip = "192.168.56.1"
server_port = 2001
mpHands = mp.solutions.hands
mpDraw = mp.solutions.drawing_utils
mpFace= mp.solutions.face_detection
class HandDetector:
    
    def __init__(self, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        #when the mediapipe is first started, it detects the hands. After that it tries to track the hands
        #as detecting is more time consuming than tracking. If the tracking confidence goes down than the
        #specified value then again it switches back to detection
        self.hands = mpHands.Hands(max_num_hands=max_num_hands, min_detection_confidence=min_detection_confidence,
                                   min_tracking_confidence=min_tracking_confidence)


    def findHandLandMarks(self, image, handNumber=0, draw=False):
        originalImage = image
        count=0
        # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # mediapipe needs RGB
        results = self.hands.process(image)
        
        handDetect=""
        if results.multi_hand_landmarks:
            if len(results.multi_handedness) == 2:
                # Display 'Both Hands' on the image
                handDetect="Both"
            
  
        # If any hand present
            else:
                for i in results.multi_handedness:
                    
                    # Return whether it is Right or Left Hand
                    label = MessageToDict(i)['classification'][0]['label']
    
                    if label == 'Left':
                        
                        # Display 'Left Hand' on
                        handDetect="Left"
                        
    
                    if label == 'Right':
                        handDetect="Right"
     

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                handIndex = results.multi_hand_landmarks.index(hand_landmarks)
                handLabel = results.multi_handedness[handIndex].classification[0].label

                if handLabel == "Left":
                    handLabel = "Right"
                elif handLabel == "Right":
                    handLabel = "Left"
                handLandmarks = []
                for landmarks in hand_landmarks.landmark:
                    imgH, imgW, imgC = originalImage.shape  # height, width, channel for image
                    # xPos, yPos = int(landmarks.x * imgW), int(landmarks.y * imgH)
        
                    handLandmarks.append([landmarks.x, landmarks.y,handLabel])
                if draw:
                    mpDraw.draw_landmarks(originalImage, hand_landmarks, mpHands.HAND_CONNECTIONS)
                
                if(len(handLandmarks) != 0):

                    if handLandmarks[4][2] == "Right" and handLandmarks[4][0] > handLandmarks[3][0]:       #Right Thumb
                        count = count+1
                        
                    elif handLandmarks[4][2] == "Left" and handLandmarks[4][0] < handLandmarks[3][0]:       #Left Thumb
                        count = count+1
                        
                    if handLandmarks[8][1] < handLandmarks[6][1]:       #Index finger
                        count = count+1
                    if handLandmarks[12][1] < handLandmarks[10][1]:     #Middle finger
                        count = count+1
                    if handLandmarks[16][1] < handLandmarks[14][1]:     #Ring finger
                        count = count+1
                    if handLandmarks[20][1] < handLandmarks[18][1]:     #Little finger
                        count = count+1

        return count,handDetect


class MainWindow(tk.Frame):
    """ Main Window """

    def __init__(self, master):
        """ Default constructor, initializes variables """
        self.master = master

        # initialize tk frame
        tk.Frame.__init__(self, master)
        
        # initialize variables

        self.isConnected = False
        self.ip = tk.StringVar(value=server_ip)
        self.port = tk.IntVar(value=server_port)
        self.video_label = tk.StringVar()
        self.additional_label = ""
        self.time_start = 0
        self.label = []
        


        # create GUI
        self.initialize_gui()

        

    def initialize_gui(self):
        """ Initializes GUI """
        self.master.title('Server')
        self.pack(fill=tk.BOTH, expand=True)

        # frame for robot network configuration
        frame_robot_config = tk.Frame(self)
        frame_robot_config.pack(fill=tk.X)
        tk.Button(frame_robot_config, text="Connect", command=self.connect).pack(side=tk.RIGHT, padx=5, pady=5)
        input_font = tkinter.font.Font(family="Arial", size=10)
        port = tk.Entry(frame_robot_config, width=6, font=input_font, textvariable=self.port)
        port.pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Label(frame_robot_config, text="PORT").pack(side=tk.RIGHT, padx=5, pady=5)
        ip = tk.Entry(frame_robot_config, width=16, font=input_font, textvariable=self.ip)
        ip.pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Label(frame_robot_config, text="IP").pack(side=tk.RIGHT, padx=5, pady=5)

        

        # frame for record and recv buttons
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(fill=tk.X)
        # send_button = tk.Button(frame_buttons, text='send', command=self.send)
        recv_button = tk.Button(frame_buttons, text='recv', command=self.recv)
        close_button = tk.Button(frame_buttons, text='Close', command=self.close, width=10)
        close_button.grid(row=0, column=1, padx=5, pady=5)
        recv_button.grid(row=0, column=0, padx=5, pady=5)
        # send_button.grid(row=0, column=0, padx=5, pady=5)

        # frame for status display
        frame_label = tk.Frame(self)
        frame_label.pack(fill=tk.X)
        self.label = tk.Label(frame_label, text="Not connected")
        self.label.pack(fill=tk.X)

    def clear_label(self):
        """ Clears label for the video """
        self.video_label.set("")
        
    def connect(self):
        """ Connect with the robot """
        # try to establish a connection
        try:        
            
            self.handDetector = HandDetector(min_detection_confidence=0.7)
            # webcamFeed = nao_socket.recv(2048)
            self.faceDetection = mpFace.FaceDetection(min_detection_confidence=0.6)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Bind the socket to the server IP address and port
            self.server_socket.bind((server_ip, server_port))

            # Listen for incoming connections
            self.server_socket.listen(1)
            print('Server listening...')

            # Accept a client connection
            self.client_socket, self.client_address = self.server_socket.accept()


            self.isConnected = True
            self.label.config(text='Ready')
            print("Connection from => ",self.client_address)
            self.secret_number=random.randint(0, 10)
            print("the secret number is",self.secret_number)
        # connecting with robot failed
        except:
            self.isConnected = False
            self.label.config(text='Not connected')

    

    
    def send(self):
        self.label.config(text='Sending....')
        """ Start recording if connected """
        if not self.isConnected:
            self.label.config(text='Not connected')
            return
        
        # print("message to send => ",self.message)
        self.client_socket.send(self.message.encode())
        self.label.config(text='is send it')
        self.recv()
            
        # elif self.count<self.secret_number:
        #     self.client_socket.send(self.message.encode())
        # else:
        #     self.client_socket.send(self.message.encode())
            

    def recv(self):
        """ Stop recording if connected and already recording """
        if not self.isConnected:
            self.label.config(text='Not connected')
            return
        self.label.config(text='Receiving....')
        result=self.client_socket.recv(2048).decode()
        # print(result)
        video_path = 'recordings/'+result  # Replace with the path to your video file
        cap = cv2.VideoCapture(video_path)
         
        # while True:   
                    
        while True:
            status, image = cap.read()
            if status:    
                self.count,handDetect = self.handDetector.findHandLandMarks(image=image, draw=True)

                imgRGB = cv2.cvtColor(image,  cv2.COLOR_BGR2RGB)
                results = self.faceDetection.process(imgRGB)
                # print(results)

                if results.detections:
                    for id,det in enumerate(results.detections):
                        bbox= det.location_data.relative_bounding_box
                        h, w, c = image.shape
                        bb= int(bbox.xmin * w), int(bbox.ymin * h),\
                            int(bbox.width * w), int(bbox.height * h)
                        cv2.rectangle(image, bb, (255,219,50), 2)
                        cv2.putText(image, f'{int(det.score[0]*100)}%',
                                    (bb[0], bb[1]-20), cv2.FONT_HERSHEY_PLAIN,
                                    2, (230,199,0), 3)
                


                cv2.putText(image, str(self.count)+" "+handDetect, (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 25)
                
                # essay=essay+1
                # Display the image using OpenCV
                cv2.imshow("Video Stream", image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break 
        # print("send now")
        
        cap.release()
        cv2.destroyAllWindows()
        self.message=''
        
        if self.count==self.secret_number:
            self.message="the number "+str(self.count)+" that you choose is the correct number"
            
        elif self.count<self.secret_number:
            self.message="oops, please choose another one,the number "+str(self.count)+" that you choose is less than the secret number"
        else:
            self.message="oops, please choose another one,the number "+str(self.count)+" that you choose is greater than the secret number"
        # self.message=("Congratulations! You have successfully chosen the correct number")
                
        # print(self.count," == ",self.message)
        # self.label.config(text='send now')
        self.send()
    
    def close(self):
        """ Stop recording and close the program """
        
        # print(self.label.cget("text"))
        if self.label.cget("text")=="Not connected":
            self.master.destroy()
        else:
            self.client_socket.close()
            self.server_socket.close()
            self.master.destroy()
        
        
    

    def to_do(self):
        """ Do stuff while in the TK main loop """
        
        self.master.after(10, self.to_do)
        
        


def main():
    """ Main function """
    # create tkinter window
    root = tk.Tk()
    main_window = MainWindow(root)
    main_window.to_do()
    root.mainloop()
    
    
    # enter tk loop
    

if __name__ == "__main__":
    main()

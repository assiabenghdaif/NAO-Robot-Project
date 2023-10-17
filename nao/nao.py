from naoqi import ALProxy
import time
import Tkinter as tk
import tkFont
import os
import threading
import socket
import subprocess



nao_ip = "192.168.3.59"
server_ip = "192.168.56.1"
server_port = 2001
filenameDest=""
class MainWindow(tk.Frame):
    """ Main Window """

    def __init__(self, master):
        """ Default constructor, initializes variables """
        self.master = master

        # initialize tk frame
        tk.Frame.__init__(self, master)
        
        # initialize variables
        self.isRecordingVideo = False
        self.isRecordingAudio = False
        self.isRecordingSonar = False
        self.isRecordingTactile = False
        self.recordTactile = tk.IntVar()
        self.recordSonar = tk.IntVar()
        self.isConnected = False
        self.ip = tk.StringVar(value=nao_ip)
        self.port = tk.IntVar(value=9559)
        self.video_label = tk.StringVar()
        self.additional_label = ""
        self.camera_dict = {0: 'Top', 1: 'Bottom'}
        self.audio_dict = {0: '.wav', 1:'.ogg'}
        self.audio_id = 0
        self.time_start = 0

        self.camera_label = []
        self.audio_label = []
        self.label = []
        self.log_sonar = []
        self.log_tactile = []

        # create GUI
        self.initialize_gui()

        # create naoqi proxies
        self.videoRecorderProxy = []
        self.audioRecorderProxy = []
        self.sonarProxy = []
        self.memoryProxy = []
        self.motion_proxy = ALProxy("ALMotion",  self.ip.get(), self.port.get())
        self.tts_proxy = ALProxy("ALTextToSpeech", self.ip.get(), self.port.get()) 
        self.posture_proxy = ALProxy("ALRobotPosture",self.ip.get(), self.port.get())
        self.posture_proxy.goToPosture("Stand", 0.5)
        self.leds = ALProxy("ALLeds", self.ip.get(), self.port.get())
        self.animated_speech = ALProxy("ALAnimatedSpeech", self.ip.get(), self.port.get())



    def initialize_gui(self):
        """ Initializes GUI """
        self.master.title('NAO audio video recorder')
        self.pack(fill=tk.BOTH, expand=True)

        # frame for robot network configuration
        frame_robot_config = tk.Frame(self)
        frame_robot_config.pack(fill=tk.X)
        tk.Button(frame_robot_config, text="Connect", command=self.connect).pack(side=tk.RIGHT, padx=5, pady=5)
        input_font = tkFont.Font(family="Arial", size=10)
        port = tk.Entry(frame_robot_config, width=6, font=input_font, textvariable=self.port)
        port.pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Label(frame_robot_config, text="PORT").pack(side=tk.RIGHT, padx=5, pady=5)
        ip = tk.Entry(frame_robot_config, width=16, font=input_font, textvariable=self.ip)
        ip.pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Label(frame_robot_config, text="IP").pack(side=tk.RIGHT, padx=5, pady=5)

        # frame for camera and audio format selection
        frame_camera_config = tk.Frame(self)
        frame_camera_config.pack(fill=tk.X)
        self.camera_label = tk.Label(frame_camera_config, text="Top", width=8)
        self.camera_label.pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Button(frame_camera_config, text="Switch camera",
                  command=self.switch_camera).pack(side=tk.RIGHT, padx=5, pady=5)
        # self.audio_label = tk.Label(frame_camera_config, text=".wav")
        # self.audio_label.pack(side=tk.RIGHT, padx=5, pady=5)
        # tk.Button(frame_camera_config, text="Switch audio",
        #           command=self.switch_audio).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # additional video label selection
        # frame_video_label = tk.Frame(self)
        # frame_video_label.pack(fill=tk.X)
        # tk.Button(frame_video_label, text='Clear', command=self.clear_label,
        #           width = 10).pack(side=tk.RIGHT, padx=5, pady=5)
        # tk.Entry(frame_video_label, width=20, font=input_font,
        #          textvariable=self.video_label).pack(side=tk.RIGHT, padx=5, pady=5)
        # tk.Label(frame_video_label, text="Video label").pack(side=tk.RIGHT, padx=5, pady=5)

        # checkboxes for sonar and tactile sensors readings
        # frame_checkboxes = tk.Frame(self)
        # frame_checkboxes.pack(fill=tk.X)
        # tk.Checkbutton(frame_checkboxes, text="Record tactile sensors",
        #                variable=self.recordTactile).pack(side=tk.RIGHT, padx=5, pady=5)
        # tk.Checkbutton(frame_checkboxes, text="Record sonar readings",
        #                variable=self.recordSonar).pack(side=tk.RIGHT, padx=5, pady=5)

        # frame for record and stop buttons
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(fill=tk.X)
        # start_button = tk.Button(frame_buttons, text='Start recording', command=self.start)
        # stop_button = tk.Button(frame_buttons, text='Stop recording', command=self.stop)
        close_button = tk.Button(frame_buttons, text='Close', command=self.close, width=10)
        recv_button = tk.Button(frame_buttons, text='Recv', command=self.receive, width=10)
        close_button.grid(row=0, column=1, padx=5, pady=5)
        # stop_button.grid(row=0, column=1, padx=5, pady=5)
        # start_button.grid(row=0, column=0, padx=5, pady=5)
        recv_button.grid(row=0,column=0, padx=5, pady=5)

        # frame for status display
        frame_label = tk.Frame(self)
        frame_label.pack(fill=tk.X)
        self.label = tk.Label(frame_label, text="Not connected")
        self.label.pack(fill=tk.X)

    # def clear_label(self):
    #     """ Clears label for the video """
    #     self.video_label.set("")
        
    def connect(self):
        """ Connect with the robot """
        # try to establish a connection
        self.label.config(text='Connected')
        try:        
            self.videoRecorderProxy = ALProxy("ALVideoRecorder", self.ip.get(), self.port.get())
            self.videoRecorderProxy.setResolution(2)
            self.videoRecorderProxy.setFrameRate(30)
            self.videoRecorderProxy.setVideoFormat("MJPG")
            self.videoRecorderProxy.setCameraID(0)
            self.audioRecorderProxy = ALProxy("ALAudioDevice", self.ip.get(), self.port.get())
            self.memoryProxy = ALProxy("ALMemory", self.ip.get(), self.port.get())
            self.sonarProxy = ALProxy("ALSonar", self.ip.get(), self.port.get())
            # Set the head pitch and yaw angles to make Nao look straight ahead
            head_pitch_angle = 0.0  # Adjust as needed
            head_yaw_angle = 0.0  # Adjust as needed
            speed = 0.5  # Adjust the speed of the movement if desired

            # Set the angles for the head movement
            names = ["HeadYaw", "HeadPitch"]
            angles = [head_yaw_angle, head_pitch_angle]
            fraction_max_speed = speed

            # Move the head to the desired angles
            self.motion_proxy.setAngles(names, angles, fraction_max_speed)

            self.animated_speech.say("Hello, I am NAO robot!")
            # self.motion_proxy = ALProxy("ALMotion",  self.ip.get(), self.port.get())
            self.animated_speech.say("let's play a game, Please show your hands to the camera to choose a number between 0 and 10")

            self.isConnected = True
            self.label.config(text='Ready')
            self.start()
            # self.stop()
            t1 = threading.Thread(target=self.animated_speech.say, args=("do you think you choose the correct number ",))
            t2 = threading.Thread(target=self.stop)


            t2.start()
            t1.start()
            t2.join()  # Wait for say thread to finish
            # self.motion_proxy.stopMove() 
        # connecting with robot failed
        except:
            self.isConnected = False
            self.label.config(text='Not connected')

    def getProxyMo(self):
        return self.motion_proxy.get()

    def connectServer(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((server_ip, server_port))
        

    def switch_camera(self):
        """ Change the recording device on the robot """
        # switch camera if connected
        if self.isConnected and not self.isRecordingVideo:
            self.videoRecorderProxy.setCameraID(1 - self.videoRecorderProxy.getCameraID())
            self.camera_label.config(text=self.camera_dict[self.videoRecorderProxy.getCameraID()])

    def raiseHand(self):
    
        names = list()
        times = list()
        keys = list()

        names.append("HeadPitch")
        times.append([0.8, 1.56, 2.24, 2.8, 3.48, 4.6])
        keys.append([[0.29602, [3, -0.266667, 0], [3, 0.253333, 0]], [-0.170316, [3, -0.253333, 0.111996], [3, 0.226667, -0.100207]], [-0.340591, [3, -0.226667, 0], [3, 0.186667, 0]], [-0.0598679, [3, -0.186667, 0], [3, 0.226667, 0]], [-0.193327, [3, -0.226667, 0], [3, 0.373333, 0]], [-0.01078, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("HeadYaw")
        times.append([0.8, 1.56, 2.24, 2.8, 3.48, 4.6])
        keys.append([[-0.135034, [3, -0.266667, 0], [3, 0.253333, 0]], [-0.351328, [3, -0.253333, 0.0493864], [3, 0.226667, -0.0441878]], [-0.415757, [3, -0.226667, 0.00372364], [3, 0.186667, -0.00306653]], [-0.418823, [3, -0.186667, 0.00306653], [3, 0.226667, -0.00372364]], [-0.520068, [3, -0.226667, 0], [3, 0.373333, 0]], [-0.375872, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("LElbowRoll")
        times.append([0.72, 1.48, 2.16, 2.72, 3.4, 4.52])
        keys.append([[-1.37902, [3, -0.24, 0], [3, 0.253333, 0]], [-1.29005, [3, -0.253333, -0.0345436], [3, 0.226667, 0.0309074]], [-1.18267, [3, -0.226667, 0], [3, 0.186667, 0]], [-1.24863, [3, -0.186667, 0.0205524], [3, 0.226667, -0.0249565]], [-1.3192, [3, -0.226667, 0], [3, 0.373333, 0]], [-1.18421, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("LElbowYaw")
        times.append([0.72, 1.48, 2.16, 2.72, 3.4, 4.52])
        keys.append([[-0.803859, [3, -0.24, 0], [3, 0.253333, 0]], [-0.691876, [3, -0.253333, -0.0137171], [3, 0.226667, 0.0122732]], [-0.679603, [3, -0.226667, -0.0122732], [3, 0.186667, 0.0101073]], [-0.610574, [3, -0.186667, 0], [3, 0.226667, 0]], [-0.753235, [3, -0.226667, 0], [3, 0.373333, 0]], [-0.6704, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("LHand")
        times.append([1.48, 4.52])
        keys.append([[0.238207, [3, -0.493333, 0], [3, 1.01333, 0]], [0.240025, [3, -1.01333, 0], [3, 0, 0]]])

        names.append("LShoulderPitch")
        times.append([0.72, 1.48, 2.16, 2.72, 3.4, 4.52])
        keys.append([[1.11824, [3, -0.24, 0], [3, 0.253333, 0]], [0.928028, [3, -0.253333, 0], [3, 0.226667, 0]], [0.9403, [3, -0.226667, 0], [3, 0.186667, 0]], [0.862065, [3, -0.186667, 0], [3, 0.226667, 0]], [0.897349, [3, -0.226667, 0], [3, 0.373333, 0]], [0.842125, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("LShoulderRoll")
        times.append([0.72, 1.48, 2.16, 2.72, 3.4, 4.52])
        keys.append([[0.363515, [3, -0.24, 0], [3, 0.253333, 0]], [0.226991, [3, -0.253333, 0.0257175], [3, 0.226667, -0.0230104]], [0.20398, [3, -0.226667, 0], [3, 0.186667, 0]], [0.217786, [3, -0.186667, -0.00669692], [3, 0.226667, 0.00813198]], [0.248467, [3, -0.226667, 0], [3, 0.373333, 0]], [0.226991, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("LWristYaw")
        times.append([1.48, 4.52])
        keys.append([[0.147222, [3, -0.493333, 0], [3, 1.01333, 0]], [0.11961, [3, -1.01333, 0], [3, 0, 0]]])

        names.append("RElbowRoll")
        times.append([0.64, 1.4, 1.68, 2.08, 2.4, 2.64, 3.04, 3.32, 3.72, 4.44])
        keys.append([[1.38524, [3, -0.213333, 0], [3, 0.253333, 0]], [0.242414, [3, -0.253333, 0], [3, 0.0933333, 0]], [0.349066, [3, -0.0933333, -0.0949577], [3, 0.133333, 0.135654]], [0.934249, [3, -0.133333, 0], [3, 0.106667, 0]], [0.680678, [3, -0.106667, 0.141383], [3, 0.08, -0.106037]], [0.191986, [3, -0.08, 0], [3, 0.133333, 0]], [0.261799, [3, -0.133333, -0.0698132], [3, 0.0933333, 0.0488692]], [0.707216, [3, -0.0933333, -0.103967], [3, 0.133333, 0.148524]], [1.01927, [3, -0.133333, -0.0664734], [3, 0.24, 0.119652]], [1.26559, [3, -0.24, 0], [3, 0, 0]]])

        names.append("RElbowYaw")
        times.append([0.64, 1.4, 2.08, 2.64, 3.32, 3.72, 4.44])
        keys.append([[-0.312978, [3, -0.213333, 0], [3, 0.253333, 0]], [0.564471, [3, -0.253333, 0], [3, 0.226667, 0]], [0.391128, [3, -0.226667, 0.0395378], [3, 0.186667, -0.0325606]], [0.348176, [3, -0.186667, 0], [3, 0.226667, 0]], [0.381923, [3, -0.226667, -0.0337477], [3, 0.133333, 0.0198516]], [0.977384, [3, -0.133333, 0], [3, 0.24, 0]], [0.826783, [3, -0.24, 0], [3, 0, 0]]])

        names.append("RHand")
        times.append([1.4, 3.32, 4.44])
        keys.append([[0.853478, [3, -0.466667, 0], [3, 0.64, 0]], [0.854933, [3, -0.64, 0], [3, 0.373333, 0]], [0.425116, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("RShoulderPitch")
        times.append([0.64, 1.4, 2.08, 2.64, 3.32, 4.44])
        keys.append([[0.247016, [3, -0.213333, 0], [3, 0.253333, 0]], [-1.17193, [3, -0.253333, 0], [3, 0.226667, 0]], [-1.0891, [3, -0.226667, 0], [3, 0.186667, 0]], [-1.26091, [3, -0.186667, 0], [3, 0.226667, 0]], [-1.14892, [3, -0.226667, -0.111982], [3, 0.373333, 0.184441]], [1.02015, [3, -0.373333, 0], [3, 0, 0]]])

        names.append("RShoulderRoll")
        times.append([0.64, 1.4, 2.08, 2.64, 3.32, 4.44])
        keys.append([[-0.242414, [3, -0.213333, 0], [3, 0.253333, 0]], [-0.954191, [3, -0.253333, 0], [3, 0.226667, 0]], [-0.460242, [3, -0.226667, 0], [3, 0.186667, 0]], [-0.960325, [3, -0.186667, 0], [3, 0.226667, 0]], [-0.328317, [3, -0.226667, -0.0474984], [3, 0.373333, 0.0782326]], [-0.250085, [3, -0.373333, 0], [3, 0, 0]]])

        
        names.append("RWristYaw")
        times.append([1.4, 3.32, 4.44])
        keys.append([[-0.312978, [3, -0.466667, 0], [3, 0.64, 0]], [-0.303775, [3, -0.64, -0.00920312], [3, 0.373333, 0.00536849]], [0.182504, [3, -0.373333, 0], [3, 0, 0]]])
        # tts_proxy.say("Hi")
        self.motion_proxy.angleInterpolationBezier(names, times, keys)

    def say(self,text):
        # self.tts_proxy.setParameter("bodyLanguageMode", "contextual")
        self.tts_proxy.say(text)
    
    def switch_audio(self):
        
        """ Change the format of audio recording
            .ogg is a single channel recording from the front microphone
            .wav (default) is a 4-channel recording from all microphones
        """
        if not self.isRecordingAudio:
            self.audio_id = 1 - self.audio_id
            self.audio_label.config(text=self.audio_dict[self.audio_id])

    def start(self):
        
        """ Start recording if connected """
        if not self.isConnected:
            self.label.config(text='Not connected')
            return
        
        # use timestamped filenames
        filename = time.strftime("%Y%m%d_%H%M%S")+"_video"
        filename_audio = filename+self.audio_dict[self.audio_id]

        # start recording
        self.videoRecorderProxy.startRecording("/home/nao/recordings/", filename)
        self.filenameDest=filename+".avi"
        self.isRecordingVideo = True
        self.audioRecorderProxy.startMicrophonesRecording("/home/nao/recordings/"+filename_audio)
        self.isRecordingAudio = True
        self.label.config(text='Recording')
        if self.recordSonar.get():
            self.log_sonar = open('./sensor_readings/'+filename+'_sonar.txt', 'w')
            self.isRecordingSonar = True
            self.sonarProxy.subscribe("myApp")
        if self.recordTactile.get():
            self.isRecordingTactile = True
            self.log_tactile = open('./sensor_readings/'+filename+'_tactile.txt', 'w')
        
        self.time_start = time.time()
        time.sleep(10)
        

    def stop(self):
        
        """ Stop recording if connected and already recording """
        if not self.isConnected:
            self.label.config(text='Not connected')
            return
        if self.isRecordingVideo:
            self.videoRecorderProxy.stopRecording()
            self.isRecordingVideo = False
        if self.isRecordingAudio:
            self.audioRecorderProxy.stopMicrophonesRecording()
            self.isRecordingAudio = False
        if not self.isRecordingAudio and not self.isRecordingVideo:
            self.label.config(text='Recording stopped')
        if self.isRecordingSonar:
            self.isRecordingSonar = False
            self.log_sonar.close()
            self.sonarProxy.unsubscribe("myApp")
        if self.isRecordingTactile:
            self.isRecordingTactile = False
            self.log_tactile.close()
        # print(filenameDest)
        
        
        
        cmd="pscp -pw nao nao@"+nao_ip+":/home/nao/recordings/"+ self.filenameDest+" D:/NAOProject/server/recordings"
        os.system(cmd)
        
        # ret_cmd.stdin.write("nao".encode())
        # ret_cmd.stdin.flash()
        self.client_socket.send(self.filenameDest.encode())
        # time.sleep(50)
        # result=self.client_socket.recv(2048)#.decode()
        # if result : self.say(result.decode())
        
    def receive(self):
        self.label.config(text='receive....')
        receive_lab=self.client_socket.recv(1024)
        print(receive_lab)
        
        if(receive_lab=='Congratulations! You have successfully chosen the correct number'):
            configuration = {"bodyLanguageMode": "contextual"}
            self.animated_speech.say(receive_lab, configuration)

            
            
            
            # Animate the hand movements while speaking
            # self.animated_speech.say(receive_lab, configuration)

            self.label.config(text='game finished')
            self.bayFun()
        else:   
            self.animated_speech.say(receive_lab)
            self.label.config(text='start recording')
            self.start()
            t1 = threading.Thread(target=self.animated_speech.say, args=("do you think you choose the correct number ",))
            t2 = threading.Thread(target=self.stop)


            t2.start()
            t1.start()
            t2.join() 

    def close(self):
        """ Stop recording and close the program """
        if self.isRecordingVideo:
            self.videoRecorderProxy.stopRecording()
        if self.isRecordingAudio:
            self.audioRecorderProxy.stopMicrophonesRecording()
            
        t1 = threading.Thread(target=self.say, args=("Goodbye see you later",))
        t2 = threading.Thread(target=self.raiseHand)


        t2.start()
        t1.start()
        t2.join()  # Wait for say thread to finish
        self.motion_proxy.stopMove() 
        self.master.destroy()
        self.client_socket.close()
        
    def bayFun(self):
        t1 = threading.Thread(target=self.say, args=("Goodbye see you later",))
        t2 = threading.Thread(target=self.raiseHand)


        t2.start()
        t1.start()
        t2.join()  # Wait for say thread to finish
        self.motion_proxy.stopMove() 
        

    def to_do(self):
        
        """ Do stuff while in the TK main loop """
        time_stamp = time.time()-self.time_start
        if self.isRecordingSonar:
            val_left = self.memoryProxy.getData("Device/SubDeviceList/US/Left/Sensor/Value")
            val_right = self.memoryProxy.getData("Device/SubDeviceList/US/Right/Sensor/Value")
            self.log_sonar.write(str(time_stamp)+','+str(val_right)+','+str(val_left)+'\n')
        if self.isRecordingTactile:
            val_left1 = str(self.memoryProxy.getData("HandRightLeftTouched"))
            val_left2 = str(self.memoryProxy.getData("HandRightBackTouched"))
            val_left3 = str(self.memoryProxy.getData("HandRightRightTouched"))
            val_right1 = str(self.memoryProxy.getData("HandLeftLeftTouched"))
            val_right2 = str(self.memoryProxy.getData("HandLeftBackTouched"))
            val_right3 = str(self.memoryProxy.getData("HandLeftRightTouched"))
            val_head1 = str(self.memoryProxy.getData("FrontTactilTouched"))
            val_head2 = str(self.memoryProxy.getData("MiddleTactilTouched"))
            val_head3 = str(self.memoryProxy.getData("RearTactilTouched"))
            self.log_tactile.write(str(time_stamp)+',' +
                                   val_left1 + ',' + val_left2 + ','+val_left3 + ',' +
                                   val_right1 + ',' + val_right2 + ',' + val_right3 + ',' +
                                   val_head1 + ',' + val_head2 + ',' + val_head3 + '\n')
        self.master.after(10, self.to_do)
        
        


def main():
    """ Main function """
    # create tkinter window
    root = tk.Tk()
    main_window = MainWindow(root)
    main_window.connectServer()
    main_window.to_do()
    root.mainloop()
    
    
    # enter tk loop
    

if __name__ == "__main__":
    main()

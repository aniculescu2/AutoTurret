from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import RPi.GPIO as GPIO
from gpiozero import Servo
from gpiozero import RotaryEncoder
from gpiozero import Motor
from gpiozero import MotionSensor
from gpiozero.pins.pigpio import PiGPIOFactory  
from time import sleep
from time import perf_counter_ns
from time import perf_counter
import numpy as np
import threading

servo = Servo(25, pin_factory=PiGPIOFactory())
servo.min()
state = 0
e = threading.Event()
close = False
stop = True
servoThreads = []
onTarget = False

# Assigning parameter values
ppr = 350 # Pulses per half Revolution of the encoder
tsample = 0.02  #Sampling period for code execution (s)
# Encoder object with GPIO pins 14 and 15, max steps set to # of steps in half a rotation
encoder = RotaryEncoder(14, 15, max_steps=ppr, wrap=True)
anglecurr = 0
motor = Motor(forward = 23, backward = 24)

#PIR Sensors
pir1 = MotionSensor(21, queue_len=10, sample_rate=5, threshold=0.5)
#pir2 = MotionSensor(7)
#pir3 = MotionSensor(8)
pir4 = MotionSensor(20, queue_len=10, sample_rate=5, threshold=0.5)
#pir5 = MotionSensor(10)
#pir6 = MotionSensor(11)
pir7 = MotionSensor(16, queue_len=10, sample_rate=5, threshold=0.5)
#pir8 = MotionSensor(13)
#pir9 = MotionSensor(16)
pir10 = MotionSensor(12, queue_len=10, sample_rate=5, threshold=0.5)
#pir11 = MotionSensor(18)
#pir12 = MotionSensor(19)
pir13 = MotionSensor(1, queue_len=10, sample_rate=5, threshold=0.5)
#pir14 = MotionSensor(21)
#pir15 = MotionSensor(22)
pir16 = MotionSensor(7, queue_len=10, sample_rate=5, threshold=0.5)
#pir17 = MotionSensor(5)
#pir18 = MotionSensor(26)

def stopServos():
    global onTarget
    global servoThreads
    onTarget = False
    print ("closing ", len(servoThreads), " servo threads")
    for thread in servoThreads:
        thread.join()
        servoThreads.remove(thread)
 


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        global state
        global e
        global stop
        global motor
        global encoder
        global anglecurr
        global servoThreads

        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        body = post_data.decode('utf-8')
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        #self._set_response()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
	
        if body=="auto\0":
            state = 1
            self._set_response()
            self.wfile.write("Set to automatic mode ".encode('utf-8'))
            stop = False
            e.set()
        elif body == "manual\0":
            state = 0   
            self._set_response()
            self.wfile.write("Set to manual mode ".encode('utf-8'))
            e.clear()
            stop = True

        elif body == "start left\0":
            if state == 0:
                self._set_response()
                self.wfile.write("Moving left ".encode('utf-8'))
                motor.forward(.3)
            else:
                self._set_response()
                self.wfile.write("Not in manual mode ".encode('utf-8'))
        elif body == "stop left\0":
            self._set_response()
            self.wfile.write("Stopping left ".encode('utf-8'))
            motor.stop()
            
        elif body == "start right\0":
            if state == 0:
               self._set_response()
               self.wfile.write("Moving right ".encode('utf-8'))
               motor.backward(.3)
            else:
                self._set_response()
                self.wfile.write("Not in manual mode ".encode('utf-8'))
        elif body == "stop right\0":
            self._set_response()
            self.wfile.write("Stopping right ".encode('utf-8'))
            motor.stop()
            
        elif body == "start fire\0":
            if state == 0:
                self._set_response()
                self.wfile.write("Firing ".encode('utf-8'))
                servo.mid()
            else:
                self._set_response()
                self.wfile.write("Not in manual mode ".encode('utf-8'))
        elif body == "stop fire\0":
            self._set_response()
            self.wfile.write("Stopping firing ".encode('utf-8'))
            servo.min()

        else:
            self._set_response()
            self.wfile.write("Not a good command ".encode('utf-8'))

def fireServo():
    global onTarget
    while onTarget:
        servo.mid()
    servo.min()

def turnMotor(target):
    global anglecurr
    global encoder
    global motor
    global servoThreads
    global onTarget

    # PID constants
    kp = 2
    kd = 0
    ki = 0

    prevT = 0
    ePrev = 0
    eIntegral = 0
    tSample = 0.02
     
    printT = 0
    
    anglecurr = np.interp(encoder.steps, [-ppr, ppr], [360, 0])
    while abs(anglecurr - target) > 5 and stop == False:              
        #print ("current angle: ", anglecurr)
        #print ("target: ", target)
        sleep(tSample)
        currT = perf_counter_ns()
        deltaT = currT - prevT
        prevT = currT 

        anglecurr = np.interp(encoder.steps, [-ppr, ppr], [360, 0])

        error = anglecurr - target;
        if error > 180 or error < -180:
            error = -error
        #print ("Error: ", error)

        dedt = (error - ePrev)/deltaT
        eIntegral = eIntegral + error * deltaT
         
        output = kp * error + kd*dedt + ki*eIntegral
        speed = .4
        #print("output: ", output)
        if printT - currT > 1:
            print("speed: ", speed)
            printT = currT
        if output > 0:
            motor.forward(speed)
            #print ("turning left")
        elif output < 0:
            motor.backward(speed)
            #print ("turning right")
        else:
            motor.stop()
            #print ("stopping")
       
        ePrev = error
    print ("found target")
    motor.stop()
    
    # Fire servo on different thread
    onTarget = True
    servoThread = threading.Thread(target=fireServo, args=())
    servoThread.start()
    servoThreads.append(servoThread)

    

def detectMotion():
    global stop

    noMovement = perf_counter()
    activeDetections = [False, False, False, False, False, False]
    activeTimer = [noMovement, noMovement, noMovement, noMovement, noMovement, noMovement]
    while stop != True:
        # Tuple of PIR values
        # detections = (pir1.motion_detected(), pir2.motion_detected(), pir3.motion_detected(), pir4.motion_detected(), pir5.motion_detected(), pir6.motion_detected(), pir7.motion_detected(), pir8.motion_detected(), pir9.motion_detected(), pir10.motion_detected(), pir11.motion_detected(), pir12.motion_detected(), pir13.motion_detected(), pir14.motion_detected(), pir15.motion_detected(), pir16.motion_detected(), pir17.motion_detected(), pir18.motion_detected())

        try:
            detections = [pir1.motion_detected, pir4.motion_detected, pir7.motion_detected, pir10.motion_detected, pir13.motion_detected, pir16.motion_detected]
            curr_timer = perf_counter()
            for i in range(6):
                timerDiff = curr_timer - activeTimer[i]
                print ("timer diff:", timerDiff)
                if detections[i] == True:
                    if activeDetections[i] == True and timerDiff < 7 and timerDiff > 3:
                        print ("setting", i, "to false even tho true")
                        activeDetections[i] = False
                    elif activeDetections[i] == False and timerDiff > 5:
                        print ("setting", i, "to true")
                        activeDetections[i] = True
                        activeTimer[i] = curr_timer
                else:
                    activeDetections[i] = False

            # Tuple of positions corresponding to PIR locations
            positions = (60, 120, 180, 240, 300, 360)
        
            is_high = 0
            position = 0
            last = -1
            wrapped = False
            skipped = 0
        
            for i in range(6):
                # Only check for sets of 3 sensors
                if is_high >= 4:
                    break
                elif is_high > 0 and skipped >= 2:
                    print ("skipped sensors")
                    break
                
                # Check for wrap around after end of array     
                if(activeDetections[i] == True):
                    if i == 5: 
                        if wrapped == False:
                            print (i, "is true")
                            is_high = is_high + 1
                            position = position + positions[i]
                            i = -1
                        else:
                            break
                    else:
                        print (i, "is true")
                        is_high = is_high + 1
                        position = position + positions[i]

                    # Check for wrap around between beginning and end of sensor array
                    if i == 0:
                        if activeDetections[len(detections)-1] == True:
                            print (len(detections) - 1, " is true")
                            wrapped = True
                            is_high = is_high + 1
                            if activeDetections[len(detections)-2] == True:
                               print (len(detections) - 2, " is true")
                               is_high = is_high + 1
                               position = 0
                        if is_high >= 3:
                            break
                                
                    if activeDetections[i+1] == True:
                        print (i+1, " is true")
                        is_high = is_high + 1
                        position = position + positions[i+1]
                        if i+1 == 5:
                            i = -2
                        if i == 4:
                            i = -2
                        if activeDetections[i+2] == True:
                            print (i + 2, " is true")
                            is_high = is_high + 1
                            position = position + positions[i+2]
                            if i > 2:
                                i = -3
                            if activeDetections[i+3] == True:
                                print (i+3, " is true")
                                is_high = is_high + 1
                                position = position + positions[i+3]
                        break
                else:
                    print (i, "is false")
                    if is_high > 0:
                        skipped = skipped + 1
        except RuntimeError:
            print ("runtime error")
            continue
        
        if is_high > 4:
             continue
        elif is_high > 0: 
            if is_high > 1:
                position = (position+20) / is_high
            print("target position: ", position)
            turnMotor(position)
            noMovement = perf_counter()
            #sleep(1)
        elif perf_counter() - noMovement >= 2:
            stopServos()
            
    stopServos()


def wait_for_event():
    global e
    global close
    while True:
        print('Motor thread waiting for signal')
        event_is_set = e.wait()
        print('Motor thread received signal')
        e.clear()
        if (close == True):
            return
        else:
            detectMotion()

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv
    
    motorThread = threading.Thread(name='motor_thread', target=wait_for_event, args=())
    motorThread.start()
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
    close = True
    stop = True
    e.set()
    motorThread.join()
	
	#TODO: Add camera RTSP server



# AutoTurret

# Autonomous Turret Codebase

This is the code used for Alex Niculescu and Jamie Wang's ECE 590 Final Project. There are two parts, the python script run on the Raspberry Pi connected to the turret, and the Android Mobile App used to control the turret.

### Turret Server Script
The script used to directly control the turret is called ```server.py```. It has two main parts to it, the HTTP server which listens for HTTP requests, and the autonomous thread which, when activated, monitors the PIR sensors to calculate the target to rotate the turret and spins the motor accordingly as well as firing on it.

#### HTTP Server
The main thread runs an HTTP server which listens for POST requests from the mobile app and sends a response which the app receives through a GET request. There are currently 8 commands which the server will respond to.

- manual: Sets state to manual mode which deactivates sensing thread and allows user to use the other commands
- auto: Sets state to automatic mode which disables the other commands and starts the sensing thread to search and aim for a moving target
- start left: Rotates turret left
- stop left: Stops rotating turret
- start right: Rotates turret right
- stop right: Stops rotating turret
- start fire: Rotates servo motor to fire turret
- stop fire: Rotates servo back to default position

#### Sensing Thread
The script uses thread events and global flags to stop and start the sensing thread when switching between automatic and manual mode. The thread waits for a thread event so as to not waste CPU resources (like through a spinlock). Once it sees the sensing thread, it will read all of the PIR outputs, store it in a list, and then calculate the position the turret should spin to. Once the position is calcuated, it uses the encoder attached to the motor and the motor driver connected to the inputs of the motor to turn the motor to a specific position using a PID control system. Fortunately, the movements do not need to be very specific so only the Proportional part of the PID system is used, simplifying the process. Once the target postition is reached, it will rotate the servo motor by firing a joinable thread. This joinable thread will be stopped by being conditioned on a global flag, after which it will stop and all threads will be joined. The turret will fire for two seconds unless motion is detected again within that time.

### Mobile App - TurretApp

The mobile app is simple as it is mostly made of buttons and switches. To allow the user to hold a button to rotate the turret without pressing the button multiple times, an OnTouchListener is attached to the buttons rather than a OnClickListener. The OnTouchListener creates a thread to process the request rather than using the main thread so the user can continue using the app without it freezing. The thread will see if the touch action was the button being pressed down or being unpressed and will send the corresponding message to the server through a POST request (i.e. when button is pressed it will send "start left" and when it is stopped being pressed it will send "stop left"). After the POST request is sent, it will then send a GET request to see if there are any messages from the server. Under normal operation there should be a messsage saying that the action they wanted is happening (like the motor is turning left). If there is an error the server will send the error. This message is then displayed on the app screen below the "Fire" button.

### Report and Videos
Final report and presentations can be found in Report/

Demo videos can be found at https://drive.google.com/file/d/1suBEXOTCpf9pGzqy4xpqfo7rpk6urLRk/view?usp=sharing
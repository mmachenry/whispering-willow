# whispering-willow
Code to support the Weeping Willow art project at NECTR 2025

# login

    ssh ivyblossom@whisperingwillow.local #password whisperingwillow

# setup

    sudo apt install portaudio19-dev python3-pyaudio

# dev
    python -m venv venv
    source venv/bin/activate
    pip install pyaudio

# Notes on current setup
To get the project to work, boot the RaspberryPi, ensure that it's on a
WiFi network. Currently it auto logs on to PGH's WiFi and Magneato's home
but for work in the field you'll need to get it on to whatever network you
setup out there. The easiest way to do this is to use a monitor and a mouse
and use the GUI for Ubuntu.

You need the Bluetooth speak on and it should auto connect but if it doesn't
it can be finicky and your best bet is to just use the monitor and the UI
with a mouse to connect to it.

The button is connected to 3.3v on PIN 1 and GPIO PIN 4. If you're looking
at the RaspberryPI with the GPIO pins verticaly along the right side, the
pins on the left, closer to the center of the board not the outside,
counting from the top, the first pin is 1 and 4 down is 4.

Also plug in the microphone into one of the USB-A ports on the RaspberryPi.

On the actual button the underside pin and the middle pin is for connecting
the button the order doesn't matter, it's just a switch. The side pins will
connect to up to 12V but can take less if you want it to light up. It'd be
cool to connect it so that it lights up when presse and that's pretty easy
to wire. You could also just make it light up all the time.

SSH into the system and run this command:

    python /home/ivyblossom/src/whispering-willow/art.py

ary.py contains the main loop. willow.py contains the audio code. All other
code in there is tests and debugging stuff. This should play audio files
constantly and respond to the button press with a log message as well as
recording an audio file. Press and hold the button to record a secret.

Secrets are stored in /home/ivyblossom/secrets

You can copy any WAV file in there with scp if you want to add secrets to
the directory. You can also play them and delete them using just unix
commands. ffmpeg or mpv might be the easiest way to play them and listen to
what's in the directory directly without the randomness of the art.

# Further work

* Make the art.py a daemon 
* Set up an /etc/rc.local to run the program when the RaspberryPi boots.

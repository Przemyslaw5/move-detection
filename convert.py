import argparse
import threading
import ffmpeg
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("-f", "--file", help="video file path")
ap.add_argument("-s", "--send", help="true if sending to client")
args = vars(ap.parse_args())

output_filename = args["file"]
email_sending = args["send"]

# Convert video
stream = ffmpeg.input(output_filename + ".avi")
stream = ffmpeg.hflip(stream)
stream = ffmpeg.output(stream, output_filename + ".mp4")
ffmpeg.run(stream)

# Sending video to client
if email_sending == "True":
    subprocess.Popen(['python3', 'send_email.py', '-f', output_filename + '.mp4'])
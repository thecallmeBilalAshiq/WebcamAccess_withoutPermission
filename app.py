from flask import Flask, render_template
import cv2
import time
import dropbox
import threading
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)

load_dotenv()
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")


try:
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    account_info = dbx.users_get_current_account()
    print("Connected to Dropbox as:", account_info.name.display_name)
except dropbox.exceptions.AuthError as e:
    print("Error authenticating with Dropbox:", e)

def record_and_upload_and_exit():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_file = f"output_{timestamp}.mp4"

    camera = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, 20.0, (640, 480))

    print("🎥 Recording started...")
    start_time = time.time()

    while int(time.time() - start_time) < 5:
        ret, frame = camera.read()
        if not ret:
            break
        out.write(frame)

    camera.release()
    out.release()
    print(f"💾 Video saved as {output_file}")

    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        with open(output_file, "rb") as f:
            print(f"Uploading {output_file} to Dropbox...")
            upload_result = dbx.files_upload(
                f.read(),
                f"/{output_file}",
                mode=dropbox.files.WriteMode("overwrite")
            )
        print(f"✅ Uploaded {output_file} to Dropbox")
        print(f"File metadata: {upload_result}")
    except dropbox.exceptions.ApiError as e:
        print(f"❌ Dropbox API error: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")

    print("🚪 Exiting program...")
    os._exit(0)  # force exit immediately

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/counter_clicked", methods=["POST"])
def counter_clicked():
    # Start recording only once
    if not getattr(app, "recording_started", False):
        app.recording_started = True
        threading.Thread(target=record_and_upload_and_exit, daemon=True).start()
    return ("", 204)

if __name__ == "__main__":
    app.run(debug=True)

from aiohttp import web
import uuid
import argparse
import asyncio
import json
from av import VideoFrame
import logging
import time
from from_root import from_root
import cv2
import PIL.Image
import random
import os
from ultralytics import YOLO

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder

ROOT = os.path.dirname(__file__)
logger = logging.getLogger("pc")
pc = RTCPeerConnection()


face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
classes = ["bag", "human", "fire", "smoke", "number-plate"]
model = YOLO(os.path.join(ROOT, "models/best.pt"))


class VideoTransformTrack(MediaStreamTrack):
    kind = "video"
    i = 0

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track

    async def recv(self):
        # Load the pre-trained face detector

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")

        def get_infer_data(output):
            infer_data = []
            for box in output[0].boxes:
                box_data = {
                    "class": int(box.cls.numpy().data.tolist()[0]),
                    "conf": box.conf.numpy().data.tolist()[0],
                    "box": [int(p) for p in box.xyxy.numpy().data.tolist()[0]],
                }
                infer_data.append(box_data)
            return infer_data

        def overlay_prediction(img, infer_data, with_p=False):
            font_scale = 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            color = (255, 0, 0)
            thickness = 2
            line_type = cv2.LINE_AA
            probability = round(infer_data["conf"], 2)
            class_name = classes[infer_data["class"]]
            class_name_with_p = f"{class_name} {probability:.2f}"
            text = class_name_with_p if with_p else class_name
            start_point = infer_data["box"][0], infer_data["box"][1]
            org = start_point[0], start_point[1] - 15
            end_point = infer_data["box"][2], infer_data["box"][3]
            rect_drawn = cv2.rectangle(img, start_point, end_point, color, thickness)
            class_drawn = cv2.putText(
                rect_drawn, text, org, font, font_scale, color, thickness, line_type
            )
            return class_drawn

        def process_frame(frame):
            results = model(frame)
            annotated_frame = results[0].plot()
            # annot_data = get_infer_data(results)
            # annotated_frame = overlay_prediction(frame, annot_data[0])
            return annotated_frame

        def detect_faces(img):
            # Convert the image to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect faces in the image
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            if len(faces) == 0:
                return img
            # Draw rectangles around the faces
            for x, y, w, h in faces:
                img2 = cv2.rectangle(
                    img,
                    (x, y),
                    (x + w, y + h),
                    (255, 0, 0),
                    2,
                )
                # return img2
            return img2

        new_frame = VideoFrame.from_ndarray(process_frame(img), format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "index.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print("message: ", message)
            channel.send("message: " + message)

    @pc.on("track")
    def on_track(track):
        # pc.addTrack(track)

        # log_info("Track %s received", track.kind)
        # # if track.kind == "video":
        local_video = VideoTransformTrack(track)
        pc.addTrack(local_video)

    # handle offer
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


# async def on_shutdown(app):
#     # close peer connections
#     pc.close()


app = web.Application()
# app.on_shutdown.append(on_shutdown)
app.router.add_get("/", index)
app.router.add_get("/index.js", javascript)
app.router.add_post("/offer", offer)
web.run_app(app, access_log=None)

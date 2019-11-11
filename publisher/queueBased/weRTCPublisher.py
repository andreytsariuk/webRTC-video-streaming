import argparse
import asyncio
import logging
import requests 
import json
import os
import time
ROOT = os.path.dirname(__file__)
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration, 
    RTCIceServer
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling

from .cv2VideoStreamTrack import OpenCVVideoStreamTrack


pcs = set()


async def run(pc, frame_queue):
    print('RUN')
    pc.addTrack(OpenCVVideoStreamTrack(frame_queue))
    await pc.setLocalDescription(await pc.createOffer())
    URL='http://127.0.0.1:8080/offer'
    headers = {'Content-type': 'application/json',
       'Accept': 'text/plain',
       'Content-Encoding': 'utf-8'}
    data = {
        "sdp": pc.localDescription.sdp, "type": pc.localDescription.type
    }
    r = requests.post(url = URL,  data=json.dumps(data), headers=headers)
    answer = r.json() 
    print(answer)
    session = RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
    await pc.setRemoteDescription(session)
    while True:
        try:
            await asyncio.sleep(6)
        except KeyboardInterrupt:
            print( '\nkeyboardinterrupt caught (again)')
            print ('\n...Program Stopped Manually!')
            raise


def create_connection():
    pc = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(
                urls=['stun:stun.l.google.com:19302'])]))
    #pc = RTCPeerConnection()
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is %s", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.clear()
    return pc


def publishToWebRTCServer(frame_queue):

    # create peer connection
    pc = create_connection()

    # run event loop
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                frame_queue=frame_queue
            )
        )
    except KeyboardInterrupt:
        print('FINALYYYYYYY')

        pass
    finally:
        # cleanup
        loop.run_until_complete(pc.close())

import argparse
import asyncio
import logging
import math
import requests 
import cv2
import numpy
import json
from av import VideoFrame
import os
import time
ROOT = os.path.dirname(__file__)
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    RTCConfiguration, 
    RTCIceServer

)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling

pcs = set()

class webRTCPublisher:

    def __init__(self):
        self.streamTrack = FlagVideoStreamTrack()


    async def run(self, pc, player, recorder):
        pc.addTrack(self.streamTrack)
        await pc.setLocalDescription(await pc.createOffer())


        URL='http://localhost:8080/offer'
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
        await recorder.start()

    def create_connection(self, recorder):
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

    async def main(self):
        parser = argparse.ArgumentParser(description="WebRTC audio / video / data-channels demo")
        parser.add_argument("--play-from", help="Read the media from a file and sent it."),
        parser.add_argument("--record-to", help="Write received media to a file."),
        parser.add_argument("--verbose", "-v", action="count")
        #add_signaling_arguments(parser)
        args = parser.parse_args()

        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)

        # create signaling and peer connection
        #signaling = create_signaling(args)
        
        # create media source
        player = None
        
        recorder = MediaRecorder("demo-instruct.mp4")

        pc = self.create_connection(recorder)
        pcs.add(pc)
        # run event loop
        await  self.run(
                    pc=pc,
                    player=player,
                    recorder=recorder
                )

        #await   pc.close()
       



class FlagVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        self.frame = None

        print('INIT=========')


    async def add_frame(self, frame):
        colored_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.frame = VideoFrame.from_ndarray(colored_frame) 
        await asyncio.sleep(0.1)   

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        self.frame.pts = pts
        self.frame.time_base = time_base
        return self.frame





#webRTCPublisher().main()
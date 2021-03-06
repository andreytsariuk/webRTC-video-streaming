import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import datetime
import cv2
from aiohttp import web
from av import VideoFrame

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = []

tracks=[]

class MainServerStreamConfig():

    def __init__(self):
        self.main_stream = None
        self.main_track = None
        self.last_update = datetime.datetime.now().timestamp()


main_config = MainServerStreamConfig()


class CopiedVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        self.frame = None

        print('INIT=========')


    async def recv(self):
        return self

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        return frame


async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

async def style_javascript(request):
    content = open(os.path.join(ROOT, "js/style.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

async def particles_javascript(request):
    content = open(os.path.join(ROOT, "js/particles.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def check_state(request):
    if(main_config.main_stream is not None):
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"last_update": main_config.last_update}
            ),
        )
    else:
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"last_update": None}
            ),
        )

async def stream(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    track_id = params["track_id"]

    pc = RTCPeerConnection()


    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    index  = len(pcs)
    pcs.append(pc)

    print('track_id ',track_id)

    #if len(tracks) != 0 :
    #current_track = main_track 
    new_stream_track = CopiedVideoStreamTrack()
    new_stream_track.recv = main_config.main_track.recv
    pc.addTrack(new_stream_track)


    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        log_info("ICE connection state is %s", pc.iceConnectionState)
        if pc.iceConnectionState == 'closed':
            await pc.close()
            try:
                pcs.pop(index)
            except :
                pass
            
        if pc.iceConnectionState == "failed":
            await pc.close()
            try:
                pcs.pop(index)
            except :
                pass


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


async def offer(request):
    params = await request.json()

    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    #index  = len(pcs)
    #pcs.append(pc)
    main_config.main_stream = pc
    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)


    @main_config.main_stream.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @main_config.main_stream.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        log_info("ICE connection state is %s", main_config.main_stream.iceConnectionState)
        #if main_config.main_stream.iceConnectionState == 'closed':
            #await main_config.main_stream.close()
            #try:
            #   pcs.pop(index)
            #except :
            #    pass
        #if main_config.main_stream.iceConnectionState == "failed":
            #main_config.main_stream.close()
            #print('=================================FAILED=================================')

            #await pc.close()
            #try:
            #    pcs.pop(index)
            #except :
            #    pass

    @main_config.main_stream.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)
    

        print('=================================VIDEO=================================')
        main_config.last_update = datetime.datetime.now().timestamp()
        main_config.main_track = track
        main_config.main_stream.addTrack(main_config.main_track)
        
        #tracks.append(main_track)
        print('TRACK ', main_config.main_track)

        @main_config.main_track.on("ended")
        async def on_ended():
            print('=================================TRACK ENDED=================================')

            #main_config.main_track = None;
            log_info("Track %s ended", track.kind)

    # handle offer
    await main_config.main_stream.setRemoteDescription(offer)

    # send answer
    answer = await main_config.main_stream.createAnswer()
    await main_config.main_stream.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC audio / video / data-channels demo"
    )
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--write-audio", help="Write received audio to a file")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_get("/style.js", style_javascript)
    app.router.add_get("/particles.js", particles_javascript)
    app.router.add_post("/stream", stream)
    app.router.add_post("/check-state", check_state)
    app.router.add_post("/offer", offer)
    web.run_app(app, access_log=None, port=args.port, ssl_context=ssl_context)

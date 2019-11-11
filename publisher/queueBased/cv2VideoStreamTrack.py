import asyncio
import numpy
import cv2
from av import VideoFrame
from aiortc import (
    VideoStreamTrack
)



class OpenCVVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self, frame_queue):
        super().__init__()  # don't forget this!
        self.counter = 0
        self.frame_queue =frame_queue
        print('INIT=========')

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = self.frame_queue.get()
        colored_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        current_frame =VideoFrame.from_ndarray(colored_frame)

        self.frame_queue.task_done() 
        current_frame.pts = pts
        current_frame.time_base = time_base


        return current_frame
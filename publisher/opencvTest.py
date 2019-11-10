import time
import numpy as np 
import cv2 
import threading
from weRTCPublisher import webRTCPublisher
import asyncio

async def _test(pub):
    cap = cv2.VideoCapture(0)   
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    while(True): 
        ret, frame = cap.read()

        if(frame is not None):
            await pub.streamTrack.add_frame(frame)
            
            
    cap.release() 




pub = webRTCPublisher()
                               
loop = asyncio.get_event_loop()
loop.create_task(_test(pub))
loop.create_task(pub.main())
loop.run_forever()
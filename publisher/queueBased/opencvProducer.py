import cv2
from multiprocessing.pool import ThreadPool
import asyncio

async def get_frame(cap, queue):
    while True:
        ret, frame = cap.read()
        print('READ')
        queue.put(frame)
        await asyncio.sleep(0.01)
   
def init_cap(camera_id, width=1920, heigh=1080):
    cap = cv2.VideoCapture(camera_id)   
    #cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, heigh)
    return cap

def readFromCamera(queue,camera_id=0):

    loop = asyncio.new_event_loop()
    loop.run_until_complete(get_frame(init_cap(camera_id),queue))
   

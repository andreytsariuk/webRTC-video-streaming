from queue import Queue 
from threading import Thread 

from publisher.queueBased.opencvProducer import readFromCamera
from publisher.queueBased.weRTCPublisher import publishToWebRTCServer

# A thread that produces data 
def producer(out_q): 
    readFromCamera(out_q, 0) 



# A thread that consumes data 
def consumer(in_q): 
    publishToWebRTCServer(in_q)
          
# Create the shared queue and launch both threads 
q = Queue() 
t2 = Thread(target = producer, args =(q, )) 
t1 = Thread(target = consumer, args =(q, )) 
t2.start() 
t1.start() 
  
# Wait for all produced items to be consumed 
q.join() 
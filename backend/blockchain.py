import hashlib
import time

class block :
    def __init__(self,index,timeStamp,data,):
        self.index = index
        self.timeStamp = timeStamp
        self.data = data
        
        self.prevHash = None 
        self.nonce = 0
        self.hash = None
        
    def calculate_hash(self) :
        toHash=(str(self.index)+
        str(self.timeStamp)+
        str(self.data)+
        str(self.prevHash)+
        str(self.nonce)+
        str(self.hash))
        
        return hashlib.sha256(toHash.encode()).hexdigest()
    
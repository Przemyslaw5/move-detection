from abc import abstractmethod

class Framer(object):    
    @abstractmethod
    def get_frame(self):
        raise NotImplementedError
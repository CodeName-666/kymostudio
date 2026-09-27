
import serial.tools.list_ports
from PySide6.QtCore import QObject, QTimer


SerialSize = {
    '5Bit': serial.FIVEBITS, 
    '6Bit': serial.SIXBITS, 
    '7Bit': serial.SEVENBITS, 
    '8Bit': serial.EIGHTBITS
}

SerialStopBits = {
    '1Bit'  : serial.STOPBITS_ONE, 
    '1.5Bit': serial.STOPBITS_ONE_POINT_FIVE, 
    '2Bit'  : serial.STOPBITS_TWO
}

SerialParity = {
    'None' : serial.PARITY_NONE, 
    'Even' : serial.PARITY_EVEN, 
    'Odd'  : serial.PARITY_ODD, 
    'Mark' : serial.PARITY_MARK, 
    'Space': serial.PARITY_SPACE
}

def DictValue2Key(dictionary: dict, value):
    return list(dictionary.keys())[list(dictionary.values()).index(value)]

    
class SerialConfig(QObject):

    def __init__(self, default_config: dict):
        super(SerialConfig, self).__init__()

        self.__port: str = ""
        self.__baud: int = 0
        self.__size: int = 0
        self.__parity: float = 0
        self.__stopbits: str = 0

        self.__com_available_list = []
        self.__com_updater_timer = QTimer()
        self.___init_update_timer()

        self.com_list = []
        self.setup = default_config

    def load(self):
        self.__com_list = self.create_com_list()

 
    @property
    def setup(self) -> dict:
        return {
            "port"     : self.__port,
            "baud"     : self.__baud,
            "size"     : DictValue2Key(SerialSize,self.__size),
            "parity"   : DictValue2Key(SerialParity, self.__parity),
            "stop_bits": DictValue2Key(SerialStopBits, self.__stopbits)
        }
        

    @setup.setter
    def setup(self, config: dict):
        self.__port = config["port"]
        self.__baud = config["baud"]
        self.__size = SerialSize[config["size"]]
        self.__parity = SerialParity[config["parity"]]
        self.__stopbits = SerialStopBits[config["stop_bits"]]
        
   

import logging
import select
from datetime import datetime
import time
import socket


TIMEOUT_CONNECT = 10
TIMEOUT_RESPONSE = 10


LIST_OF_CLIENT = [
    {
        "name":"DET_1",
        "ip":"127.0.0.1",
        "port":1000,
        "enabled": True
    },
    {
        "name":"DET_2",
        "ip":"10.128.0.1",
        "port":151,
        "enabled": False
    }
]



LIST_OF_OK_CLIENT = []
LIST_OF_KO_CLIENT = []


def SendCommandToSlave(ip, port, cmd, run_number, unix_time, run_type):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT_CONNECT)
        s.connect((ip, port))

        data = [0xFF, 0x80, 0x00, 0x8]
        data.append( (run_number >> 8) & 0xFF )
        data.append( (run_number >> 0) & 0xFF )
        data.append( (run_type >> 8) & 0xFF )
        data.append( (run_type >> 0) & 0xFF )
        if cmd == "START":
            data.append(0xEE)
            data.append(0x0)
            data.append(0x0)
            data.append(0x1)
        else:
            data.append(0xEE)
            data.append(0x0)
            data.append(0x0)
            data.append(0x0)

        data.append( (START_UNIX_TIME >> 24) & 0xFF )
        data.append( (START_UNIX_TIME >> 16) & 0xFF )
        data.append( (START_UNIX_TIME >> 8) & 0xFF )
        data.append( (START_UNIX_TIME >> 0) & 0xFF )

        MESSAGE = bytearray(data)
        s.send(MESSAGE)

        s.setblocking(0)
        ready = select.select([s], [], [], TIMEOUT_RESPONSE)
        if ready[0]:
            data = s.recv(16)
            logging.info("Slave %s:%d. Response: %s", ip, port, data.hex())
            s.close()
            return True
        else:
            return False
    except socket.error:
        logging.info("Unable to connect to Slave: %s:%d. ERROR: %s", ip, port, socket.error)
        return False


def SendCommandToSlaves(cmd, run_number, unix_time, run_type, stop_on_error):
    good = True
    LIST_OF_OK_CLIENT.clear()
    LIST_OF_KO_CLIENT.clear()
    for c in LIST_OF_CLIENT:
        if c["enabled"]:
            logging.info("Sending: %s command to client: %s [%s:%d]", cmd, c["name"], c["ip"], c["port"])   
            if (SendCommandToSlave(c["ip"],c["port"],cmd,run_number,unix_time,run_type) == False)  :
                LIST_OF_KO_CLIENT.append(c)
                if  (stop_on_error == True):
                    return False
                else:
                    good = False
            else:
                LIST_OF_OK_CLIENT.append(c)
    
    return good

def SendCommandToFewSlaves(LC, cmd, run_number, unix_time, run_type):
    for c in LC:
        logging.info("Sending: %s command to client: %s [%s:%d]", cmd, c["name"], c["ip"], c["port"])   
        SendCommandToSlave(c["ip"],c["port"],cmd,run_number,unix_time,run_type)

    LIST_OF_OK_CLIENT.clear()
    LIST_OF_KO_CLIENT.clear()


if __name__ == '__main__':

    CURRENT_RUN_NUMBER = 15
    CURRENT_RUN_TYPE = 1
    START_UNIX_TIME = int(time.time())
    T_RUN_S = 10

    ret = SendCommandToSlaves("START", CURRENT_RUN_NUMBER, START_UNIX_TIME, CURRENT_RUN_TYPE, True)
    if ret == True:
        logging.info("All slaves ready. Starting master stats")
        logging.info("RUN %d IS STARTED!",  CURRENT_RUN_NUMBER)

        time.sleep(T_RUN_S)

        STOP_UNIX_TIME = int(time.time())
        SendCommandToSlaves("STOP", CURRENT_RUN_NUMBER, STOP_UNIX_TIME, CURRENT_RUN_TYPE, False)

    else:
        logging.info("Following slaves does not corretly started")
        for c in LIST_OF_KO_CLIENT:
            logging.info("%s",c)
        logging.info("Run can not start if all enabled slaves do not succesfully started")
        logging.info("Stop all running slaves")
        SendCommandToFewSlaves(LIST_OF_OK_CLIENT, "STOP", CURRENT_RUN_NUMBER, START_UNIX_TIME, CURRENT_RUN_TYPE)
        logging.info("RUN %d START FALIED!",  CURRENT_RUN_NUMBER)
        




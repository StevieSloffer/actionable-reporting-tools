import socket
import threading
import datetime
import re
import pytz
import logging
import database as db #internal module
import configparser

def setupLogging():
    logging.basicConfig(
        level=logging.INFO, 
        format='[%(asctime)s][%(levelname)s] -- %(message)s', 
        datefmt='%Y-%m-%d %H:%M'
    )

def convertToEst(datetimeStringUtc):
    if not datetimeStringUtc or datetimeStringUtc.lower() == 'null':
        return None
    try:
        utcTz = pytz.timezone('UTC')
        estTz = pytz.timezone('US/Eastern')
        dtFormat = '%Y/%m/%d %H:%M:%S'
        
        utcDt = datetime.datetime.strptime(datetimeStringUtc, dtFormat)
        localizedUtcDt = utcTz.localize(utcDt)
        estDt = localizedUtcDt.astimezone(estTz)
        return estDt.strftime(dtFormat)
    except (ValueError, TypeError) as e:
        logging.warning(f"LISTENER: could not convert datetime string '{datetimeStringUtc}': {e}")
        return None

def convertDurationToSeconds(durationStr):
    if not durationStr or durationStr.lower() == 'null':
        return 0
    try:
        parts = list(map(int, durationStr.split(':')))
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except (ValueError, IndexError) as e:
        logging.warning(f"LISTENER: could not convert duration string '{durationStr}': {e}")
        return 0

def processAndPrepareData(rawDataString):
    try:
        dataParts = rawDataString.split(',')
        if len(dataParts) < 27:
            logging.warning(f"LISTENER: received incomplete CDR data: {rawDataString}")
            return None

        processedData = []

        for i, value in enumerate(dataParts[:27]):
            cleanValue = value.strip()
            
            part = ''
            if i < len(dataParts):
                part = dataParts[i]
                  
            if i in [0, 1, 2, 11, 12, 13]:
                processedData.append(int(re.sub(r'\D', '', part)) if part else None)
            elif i in [3, 4, 5]:
                processedData.append(convertToEst(part))
            elif i == 6:
                processedData.append(convertDurationToSeconds(part))
            else: 
                processedData.append(part if part else None)
        
        return processedData
    except Exception as e:
        logging.error(f"LISTENER: error during data processing for '{rawDataString}': {e}")
        return None

def isAMissedCall(callDataList):
    if callDataList and len(callDataList) > 14:
        if callDataList[0] == "9900":
            return False
        if callDataList[14] is not None:
            return True      
    return False

def handleConnection(conn, addr):
    logging.info(f"LISTENER: new connection from {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                logging.info(f"LISTENER: connection closed by {addr}")
                break 

            cdrString = data.decode('utf-8').strip()
            logging.info(f"LISTENER: received data: {cdrString}")
            
            callDetails = processAndPrepareData(cdrString)
            
            if callDetails and isAMissedCall(callDetails):
                logging.info(f"LISTENER: detected a missed call for queue {callDetails[0]}. Logging to DB.")
                db.insert_missed_call(callDetails)
            else:
                logging.info(f"LISTENER: call was not a missed call. No action taken.")

    except (BrokenPipeError, ConnectionResetError):
        logging.warning(f"LISTENER: connection with {addr} was forcibly closed by the remote host.")
    except Exception as e:
        logging.error(f"LISTENER: an unexpected error occurred with connection {addr}: {e}")
    finally:
        conn.close()
        logging.info(f"LISTENER: closed connection and thread for {addr}.")

def main():
    setupLogging()
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    listener_config = config['listener']
    host = listener_config.get('host', '')
    port = int(listener_config.get('port', ''))

    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        serverSocket.bind((host, port))
        serverSocket.listen(128) #arbitarilty choosen, choose a number that makes sense for you
        
        logging.info(f"LISTENER: server started. Listening on port {port}...")

        while True:
            conn, addr = serverSocket.accept()
            
            thread = threading.Thread(target=handleConnection, args=(conn, addr))
            thread.daemon = True 
            thread.start()

    except Exception as e:
        logging.critical(f"LISTENER: a critical error occurred in the main server loop: {e}")
    finally:
        logging.info("LISTENER: shutting down server socket.")
        serverSocket.close()

if __name__ == "__main__":
    main()

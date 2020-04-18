#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import argparse
import urllib3
from threading import Thread
from urlparse import urlparse
from socket import *
from threading import Thread
from time import sleep
import random
import string
import traceback

DEBUG = False
MAX_RETRY = 30

# Constants
SOCKTIMEOUT = 5
RESENDTIMEOUT = 300
VER = "\x05"
METHOD = "\x00"
SUCCESS = "\x00"
SOCKFAIL = "\x01"
NETWORKFAIL = "\x02"
HOSTFAIL = "\x04"
REFUSED = "\x05"
TTLEXPIRED = "\x06"
UNSUPPORTCMD = "\x07"
ADDRTYPEUNSPPORT = "\x08"
UNASSIGNED = "\x09"

BASICCHECKSTRING = "Georg says, 'All seems fine'"

# Globals
READBUFSIZE = 1024

# Logging
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

LEVEL = {"INFO": logging.INFO, "DEBUG": logging.DEBUG, }

logLevel = "INFO"

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED,
    'RED': RED,
    'GREEN': GREEN,
    'YELLOW': YELLOW,
    'BLUE': BLUE,
    'MAGENTA': MAGENTA,
    'CYAN': CYAN,
    'WHITE': WHITE,
}

def random_useragent():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):

    def __init__(self, name):
        FORMAT = "[$BOLD%(levelname)-18s$RESET]  %(message)s"
        COLOR_FORMAT = formatter_message(FORMAT, True)
        logging.Logger.__init__(self, name, logLevel)
        if (name == "transfer"):
            COLOR_FORMAT = "\x1b[80D\x1b[1A\x1b[K%s" % COLOR_FORMAT
        color_formatter = ColoredFormatter(COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return

FORMAT = "%(processName)s %(threadName)s: - %(name)s - %(levelname)s - %(message)s - %(module)s"
formatter = logging.Formatter(fmt=FORMAT)                                 
handler = logging.StreamHandler()
handler.setFormatter(formatter)

#logging.setLoggerClass(ColoredLogger)
log = logging.getLogger(__name__)
log.addHandler(handler)
log.setLevel(logging.DEBUG) 
transferLog = logging.getLogger("transfer")
transferLog.addHandler(handler)
transferLog.setLevel(logging.DEBUG) 


class SocksCmdNotImplemented(Exception):
    pass


class SocksProtocolNotImplemented(Exception):
    pass


class RemoteConnectionFailed(Exception):
    pass


class session(Thread):
    def __init__(self, pSocket, connectString):
        Thread.__init__(self)
        self.pSocket = pSocket
        self.connectString = connectString
        o = urlparse(connectString)
        try:
            self.httpPort = o.port
        except:
            if o.scheme == "https":
                self.httpPort = 443
            else:
                self.httpPort = 80
        self.httpScheme = o.scheme
        self.httpHost = o.netloc.split(":")[0]
        self.httpPath = o.path
        self.cookie = None
        self.processid = None
        if o.scheme == "http":
            self.httpScheme = urllib3.HTTPConnectionPool
        else:
            self.httpScheme = urllib3.HTTPSConnectionPool

    def parseSocks5(self, sock):
        log.debug("SocksVersion5 detected")
        nmethods, methods = (sock.recv(1), sock.recv(1))
        sock.sendall(VER + METHOD)
        ver = sock.recv(1)
        if ver == "\x02":  # this is a hack for proxychains
            ver, cmd, rsv, atyp = (sock.recv(1), sock.recv(1), sock.recv(1), sock.recv(1))
        else:
            cmd, rsv, atyp = (sock.recv(1), sock.recv(1), sock.recv(1))
        target = None
        targetPort = None
        if atyp == "\x01":  # IPv4
            # Reading 6 bytes for the IP and Port
            target = sock.recv(4)
            targetPort = sock.recv(2)
            target = "." .join([str(ord(i)) for i in target])
        elif atyp == "\x03":  # Hostname
            targetLen = ord(sock.recv(1))  # hostname length (1 byte)
            target = sock.recv(targetLen)
            targetPort = sock.recv(2)
            target = "".join([unichr(ord(i)) for i in target])
        elif atyp == "\x04":  # IPv6
            target = sock.recv(16)
            targetPort = sock.recv(2)
            tmp_addr = []
            for i in xrange(len(target) / 2):
                tmp_addr.append(unichr(ord(target[2 * i]) * 256 + ord(target[2 * i + 1])))
            target = ":".join(tmp_addr)
        targetPort = ord(targetPort[0]) * 256 + ord(targetPort[1])
        if cmd == "\x02":  # BIND
            raise SocksCmdNotImplemented("Socks5 - BIND not implemented")
        elif cmd == "\x03":  # UDP
            raise SocksCmdNotImplemented("Socks5 - UDP not implemented")
        elif cmd == "\x01":  # CONNECT
            serverIp = target
            try:
                serverIp = gethostbyname(target)
            except:
                log.error("oeps")
            serverIp = "".join([chr(int(i)) for i in serverIp.split(".")])
            self.cookie, self.processid = self.setupRemoteSession(target, targetPort)
            if self.cookie:
                sock.sendall(VER + SUCCESS + "\x00" + "\x01" + serverIp + chr(targetPort / 256) + chr(targetPort % 256))
                return True
            else:
                sock.sendall(VER + REFUSED + "\x00" + "\x01" + serverIp + chr(targetPort / 256) + chr(targetPort % 256))
                raise RemoteConnectionFailed("[%s:%d] Remote failed" % (target, targetPort))

        raise SocksCmdNotImplemented("Socks5 - Unknown CMD")

    def parseSocks4(self, sock):
        log.debug("SocksVersion4 detected")
        cmd = sock.recv(1)
        if cmd == "\x01":  # Connect
            targetPort = sock.recv(2)
            targetPort = ord(targetPort[0]) * 256 + ord(targetPort[1])
            target = sock.recv(4)
            sock.recv(1)
            target = ".".join([str(ord(i)) for i in target])
            serverIp = target
            try:
                serverIp = gethostbyname(target)
            except:
                log.error("oeps")
            serverIp = "".join([chr(int(i)) for i in serverIp.split(".")])
            self.cookie = self.setupRemoteSession(target, targetPort)
            if self.cookie:
                sock.sendall(chr(0) + chr(90) + serverIp + chr(targetPort / 256) + chr(targetPort % 256))
                return True
            else:
                sock.sendall("\x00" + "\x91" + serverIp + chr(targetPort / 256) + chr(targetPort % 256))
                raise RemoteConnectionFailed("Remote connection failed")
        else:
            raise SocksProtocolNotImplemented("Socks4 - Command [%d] Not implemented" % ord(cmd))

    def handleSocks(self, sock):
        # This is where we setup the socks connection
        ver = sock.recv(1)
        if ver == "\x05":
            return self.parseSocks5(sock)
        elif ver == "\x04":
            return self.parseSocks4(sock)

    def setupRemoteSession(self, target, port):
        headers = {"X-CMD": "CONNECT", "X-TARGET": target, "X-PORT": port, "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
        self.target = target
        self.port = port
        cookie = None
        processid = None
        conn = self.httpScheme(host=self.httpHost, port=self.httpPort)
        # response = conn.request("POST", self.httpPath, params, headers)
        if DEBUG: print "[+] setupRemoteSession: POST ", self.connectString + "?cmd=connect&target=%s&port=%d" % (target, port)
        if DEBUG: print "[+] setupRemoteSession: request_headers: ", repr(headers)
        response = conn.urlopen('POST', self.connectString + "?cmd=connect&target=%s&port=%d" % (target, port), headers=headers, body="", redirect=False)
        if DEBUG: print "[+] setupRemoteSession: response.status:", response.status
        if DEBUG: print "[+] setupRemoteSession: response.headers:", response.headers
        if response.status == 200:
            status = response.getheader("x-status")
            if status == "OK":
                cookie = response.getheader('X-SESSIONID')
                processid = response.getheader('X-PROCESSID')
                log.info("[%s:%d] setupRemoteSession HTTP [200]: cookie [%s], processid [%s]" % (self.target, self.port, cookie, processid))
            else:
                if response.getheader("X-ERROR") is not None:
                    log.error(response.getheader("X-ERROR"))
        else:
            log.error("[%s:%d] HTTP [%d]: [%s]" % (self.target, self.port, response.status, response.getheader("X-ERROR")))
            log.error("[%s:%d] RemoteError: %s" % (self.target, self.port, response.data))
        conn.close()
        return (cookie, processid)

    def closeRemoteSession(self):
        num_retry = 0
        while num_retry < MAX_RETRY:
            headers = {"X-CMD": "DISCONNECT", "Cookie": self.cookie, "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
            params = ""
            conn = self.httpScheme(host=self.httpHost, port=self.httpPort)
            if DEBUG: print "[+] closeRemoteSession: POST " + self.httpPath + "?cmd=disconnect&processid="+self.processid+"&sessionid="+self.cookie
            if DEBUG: print "[+] closeRemoteSession: request_headers: " + repr(headers)
            response = conn.request("POST", self.httpPath + "?cmd=disconnect&processid="+self.processid+"&sessionid="+self.cookie, params, headers, redirect=False)
            if DEBUG: print "[+] closeRemoteSession: response.status:", response.status
            if DEBUG: print "[+] closeRemoteSession: response.headers:", response.headers
            if response.status == 200:
                status = response.getheader("x-status")
                conn.close()
                if status == "OK":
                    log.info("[%s:%d] closeRemoteSession cookie [%s], processid [%s], Connection Terminated" % (self.target, self.port, self.cookie, self.processid))
                    break # finish retry loop
                elif status == "RETRY":
                    num_retry += 1
                    continue
                else:
                    log.error("[%s:%d] cookie [%s], processid [%s], HTTP [%d]: Status: [%s]: Message [%s] Shutting down" % (self.target, self.port, self.cookie, self.processid, response.status, status, response.getheader("X-ERROR")))
                    break # finish retry loop
            else:
                conn.close()
                log.error("[%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status))
                break # finish retry loop
        

    def reader(self):
        #conn = urllib3.PoolManager()
        headers = {"X-CMD": "READ", "Cookie": self.cookie, "Connection": "Keep-Alive", "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
        while True:
            try:
                if not self.pSocket:
                    break
                data = ""
                num_retry = 0
                while num_retry < MAX_RETRY:
                    if DEBUG: print "[+] Try to read data, num_retry = %d" % num_retry
                    if DEBUG: print "[+] reader: POST " + self.connectString + "?cmd=read&processid="+self.processid+"&sessionid="+self.cookie
                    if DEBUG: print "[+] reader: request_headers: " + repr(headers)
                    conn = self.httpScheme(host=self.httpHost, port=self.httpPort)
                    response = conn.request('POST', self.connectString + "?cmd=read&processid="+self.processid+"&sessionid="+self.cookie, headers=headers, body="", redirect=False)
                    if DEBUG: print "[+] reader: response.status:", response.status
                    if DEBUG: print "[+] reader: response.headers:", response.headers
                    data = None
                    if response.status == 200:
                        status = response.getheader("x-status")
                        conn.close()
                        if status == "OK":
                            data = response.data
                            # Yes I know this is horrible, but its a quick fix to issues with tomcat 5.x bugs that have been reported, will find a propper fix laters
                            try:
                                if response.getheader("server").find("Apache-Coyote/1.1") > 0:
                                    data = data[:len(data) - 1]
                            except:
                                pass
                            if data is None:
                                data = ""
                            #log.info("[%s:%d] reader , cookie [%s], processid [%s], retry [%d]" % (self.target, self.port, self.cookie, self.processid, num_retry))
                            break # finish retry loop
                        elif status == "RETRY":
                            # retry another worker process
                            num_retry += 1
                            headers = {"X-CMD": "READ", "Cookie": self.cookie, "Connection": "Keep-Alive", "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
                            continue
                        else:
                            data = None
                            log.error("[%s:%d] HTTP [%d]: Status: [%s]: Message [%s] Shutting down" % (self.target, self.port, response.status, status, response.getheader("X-ERROR")))
                            break # finish retry loop
                    else:
                        conn.close()
                        log.error("[%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status))
                        break # finish retry loop

                if data is None:
                    # Remote socket closed
                    break
                if len(data) == 0:
                    sleep(0.1)
                    continue
                transferLog.info("[%s:%d] reader, cookie [%s], processid [%s] <<<< [%d]" % (self.target, self.port, self.cookie, self.processid, len(data)))
                self.pSocket.send(data)
            except Exception, ex:
                traceback.print_exc()
                raise ex
        self.closeRemoteSession()
        log.debug("[%s:%d] Closing localsocket" % (self.target, self.port))
        try:
            self.pSocket.close()
        except:
            log.debug("[%s:%d] Localsocket already closed" % (self.target, self.port))

    def writer(self):
        global READBUFSIZE
        #conn = urllib3.PoolManager()
        headers = {"X-CMD": "FORWARD", "Cookie": self.cookie, "Content-Type": "application/octet-stream", "Connection": "Keep-Alive", "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
        while True:
            try:
                self.pSocket.settimeout(1)
                data = self.pSocket.recv(READBUFSIZE)
                if not data:
                    break
                num_retry = 0
                while num_retry < MAX_RETRY:
                    if DEBUG: print "[+] Try to send data, num_retry = %d" % num_retry
                    if DEBUG: print "[+] writer: POST " + self.connectString + "?cmd=forward&processid="+self.processid+"&sessionid="+self.cookie
                    if DEBUG: print "[+] writer: request_headers: " + repr(headers)
                    conn = self.httpScheme(host=self.httpHost, port=self.httpPort)
                    response = conn.urlopen('POST', self.connectString + "?cmd=forward&processid="+self.processid+"&sessionid="+self.cookie, headers=headers, body=data, redirect=False)
                    if DEBUG: print "[+] writer: response.status:", response.status
                    if DEBUG: print "[+] writer: response.headers:", response.headers
                    if response.status == 200:
                        status = response.getheader("x-status")
                        conn.close()
                        if status == "OK":
                            log.info("[%s:%d] writer , cookie [%s], processid [%s], retry [%d]" % (self.target, self.port, self.cookie, self.processid, num_retry))
                            transferLog.info("[%s:%d] writer, cookie [%s], processid [%s] >>>> [%d]" % (self.target, self.port, self.cookie, self.processid, len(data)))
                            break # finish retry loop
                        elif status == "RETRY":
                            # retry another worker process
                            num_retry += 1
                            headers = {"X-CMD": "FORWARD", "Cookie": self.cookie, "Content-Type": "application/octet-stream", "Connection": "Keep-Alive", "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
                            continue
                        else:
                            log.error("[%s:%d] HTTP [%d]: Status: [%s]: Message [%s] Shutting down" % (self.target, self.port, response.status, status, response.getheader("x-error")))
                            break  # finish retry loop
                    else:
                        conn.close()
                        log.error("[%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status))
                        break  # finish retry loop
            except timeout:
                continue
            except Exception, ex:
                traceback.print_exc()
                raise ex
                break
        self.closeRemoteSession()
        log.debug("Closing localsocket")
        try:
            self.pSocket.close()
        except:
            log.debug("Localsocket already closed")

    def run(self):
        try:
            if self.handleSocks(self.pSocket):
                log.debug("Starting reader")
                r = Thread(target=self.reader, args=())
                r.start()
                log.debug("Starting writer")
                w = Thread(target=self.writer, args=())
                w.start()
                r.join()
                w.join()
        except SocksCmdNotImplemented, si:
            log.error(si.message)
            self.pSocket.close()
        except SocksProtocolNotImplemented, spi:
            log.error(spi.message)
            self.pSocket.close()
        except Exception, e:
            log.error(e.message)
            if self.cookie:
                self.closeRemoteSession()
            self.pSocket.close()


def askGeorg(connectString):
    connectString = connectString
    o = urlparse(connectString)
    try:
        httpPort = o.port
    except:
        if o.scheme == "https":
            httpPort = 443
        else:
            httpPort = 80
    httpScheme = o.scheme
    httpHost = o.netloc.split(":")[0]
    httpPath = o.path
    if o.scheme == "http":
        httpScheme = urllib3.HTTPConnectionPool
    else:
        httpScheme = urllib3.HTTPSConnectionPool

    conn = httpScheme(host=httpHost, port=httpPort)
    response = conn.request("GET", httpPath)
    if response.status == 200:
        if BASICCHECKSTRING == response.data.strip():
            log.info(BASICCHECKSTRING)
            return True
    conn.close()
    return False

if __name__ == '__main__':
    print """willem@sensepost.com / @_w_m__
  sam@sensepost.com / @trowalts
  etienne@sensepost.com / @kamp_staaldraad
   """
    log.setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(description='Socks server for reGeorg HTTP(s) tunneller')
    parser.add_argument("-l", "--listen-on", metavar="", help="The default listening address", default="127.0.0.1")
    parser.add_argument("-p", "--listen-port", metavar="", help="The default listening port", type=int, default="8888")
    parser.add_argument("-r", "--read-buff", metavar="", help="Local read buffer, max data to be sent per POST", type=int, default="1024")
    parser.add_argument("-u", "--url", metavar="", required=True, help="The url containing the tunnel script")
    parser.add_argument("-v", "--verbose", metavar="", help="Verbose output[INFO|DEBUG]", default="INFO")
    args = parser.parse_args()
    if (args.verbose in LEVEL):
        log.setLevel(LEVEL[args.verbose])
        log.info("Log Level set to [%s]" % args.verbose)

    log.info("Starting socks server [%s:%d], tunnel at [%s]" % (args.listen_on, args.listen_port, args.url))
    log.info("Checking if Georg is ready")
    if not askGeorg(args.url):
        log.info("Georg is not ready, please check url")
        exit()
    READBUFSIZE = args.read_buff
    servSock = socket(AF_INET, SOCK_STREAM)
    servSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    servSock.bind((args.listen_on, args.listen_port))
    servSock.listen(1000)
    while True:
        try:
            sock, addr_info = servSock.accept()
            sock.settimeout(SOCKTIMEOUT)
            log.debug("Incomming connection")
            session(sock, args.url).start()
        except KeyboardInterrupt, ex:
            break
        except Exception, e:
            log.error(e)
    servSock.close()

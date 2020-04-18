#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import argparse
import urllib3
from threading import Thread
from urlparse import urlparse
from socket import *
import select
from threading import Thread
from time import sleep
import random
import string
import traceback
import requests
import os
import base64

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

''' 
https://stackoverflow.com/questions/38987/how-to-merge-two-dictionaries-in-a-single-expression
'''
def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


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


FORMAT = "%(levelname)-5s - %(message)s"
formatter = logging.Formatter(fmt=FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# logging.setLoggerClass(ColoredLogger)
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
        self.pSocket.settimeout(SOCKTIMEOUT)
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
        self.closed = False
        if o.scheme == "http":
            self.httpScheme = urllib3.HTTPConnectionPool
        else:
            self.httpScheme = urllib3.HTTPSConnectionPool

    def parseSocks5(self, sock):
        # log.debug("SocksVersion5 detected")
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
            target = ".".join([str(ord(i)) for i in target])
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
        global args

        log.debug('[%s:%d] SetupRemoteSession' % (target, port))

        headers = {"X-CMD": "CONNECT", "X-TARGET": target, "X-PORT": str(port), "Cookie": args.cookie,
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
        self.target = target
        self.port = port
        cookie = None
        processid = None
        conn = self.httpScheme(host=self.httpHost, port=self.httpPort)
        if DEBUG: print "[+] setupRemoteSession: POST ", self.connectString + "?cmd=connect&target=%s&port=%d" % (
            target, port)
        if DEBUG: print "[+] setupRemoteSession: request_headers: ", repr(headers)
        response = requests.post(self.connectString + "?cmd=connect&target=%s&port=%d" % (target, port),
            data=args.post_data, headers=headers, allow_redirects=False, verify=False)
        if DEBUG: print "[+] setupRemoteSession: response.status_code:", response.status_code
        if DEBUG: print "[+] setupRemoteSession: response.headers:", response.headers

        if response.status_code == 200:
            status = response.headers["x-status"]
            if status == "OK":
                cookie = response.headers['X-SESSIONID']
                processid = response.headers['X-PROCESSID']
                log.debug('[%s:%d] [%s:%s] SetupRemoteSession - OK' % (self.target, self.port, cookie, processid))
            else:
                if response.headers["X-ERROR"] is not None:
                    log.error("[%s:%d] SetupRemoteSession - ERROR - %s" % (self.target, self.port, response.headers["X-ERROR"]))
        else:
            log.error("[%s:%d] SetupRemoteSession - Code: %d | Message: %s | Data: %s" % (
                self.target, self.port, response.status_code, response.headers["X-ERROR"], response.content))

        return (cookie, processid)

    def closeRemoteSession(self):
        global args

        if self.closed:
            log.debug("[%s:%d] [%s:%s] CloseRemoteSession - Connection already closed" % (self.target, self.port, self.cookie, self.processid))
            return

        num_retry = 0
        while num_retry < MAX_RETRY:
            headers = {"X-CMD": "DISCONNECT", "Cookie": str(self.cookie) + ';' + args.cookie,
                       "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
            params = ""
            if DEBUG: log.debug(
                "[+] closeRemoteSession: POST " + self.connectString + "?cmd=disconnect&processid=" + self.processid + "&sessionid=" + self.cookie)
            if DEBUG: log.debug("[+] closeRemoteSession: request_headers: " + repr(headers))
            response = requests.post(
                self.connectString + "?cmd=disconnect&processid=" + self.processid + "&sessionid=" + self.cookie,
                data = args.post_data, headers=headers, allow_redirects=False, verify=False)
            if DEBUG: log.debug("[+] closeRemoteSession: response.status_code:", response.status_code)
            if DEBUG: log.debug("[+] closeRemoteSession: response.headers:", response.headers)
            if response.status_code == 200:
                status = response.headers["x-status"]
                if status == "OK":
                    log.info("[%s:%d] [%s:%s] CloseRemoteSession - OK" % (
                        self.target, self.port, self.cookie, self.processid))
                    break  # finish retry loop
                elif status == "RETRY":
                    log.info("[%s:%d] [%s:%s] CloseRemoteSession - RETRY" % (
                        self.target, self.port, self.cookie, self.processid))
                    num_retry += 1
                    continue
                else:
                    log.error(
                        "[%s:%d] [%s:%s] CloseRemoteSession - ERROR - Code: %d | Status: %s | Message: %s" % (
                            self.target, self.port, self.cookie, self.processid, response.status_code, status,
                            response.headers["X-ERROR"]))
                    break  # finish retry loop
            else:
                log.error("[%s:%d] CloseRemoteSession - ERROR - Code: %d | Data: %s" % (
                    self.target, self.port, response.status_code, response.content))
                break  # finish retry loop

        self.closed = True

    def reader(self):
        global args
        # conn = urllib3.PoolManager()
        headers = {"X-CMD": "READ", "Cookie": str(self.cookie) + ';' + args.cookie, "Connection": "Keep-Alive",
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
        while not self.closed:
            try:
                if not self.pSocket:
                    break
                data = ""
                num_retry = 0
                while num_retry < MAX_RETRY:
                    if DEBUG: log.debug("[+] Try to read data, num_retry = %d" % num_retry)
                    if DEBUG: log.debug(
                        "[+] reader: POST " + self.connectString + "?cmd=read&processid=" + self.processid + "&sessionid=" + self.cookie)
                    if DEBUG: log.debug("[+] reader: request_headers: " + repr(headers))
                    response = requests.post(
                        self.connectString + "?cmd=read&processid=" + self.processid + "&sessionid=" + self.cookie,
                        data = args.post_data, headers=headers, allow_redirects=False, verify=False)
                    if DEBUG: log.debug("[+] reader: response.status_code:", response.status_code)
                    if DEBUG: log.debug("[+] reader: response.headers:", response.headers)
                    data = None
                    if response.status_code == 200:
                        status = response.headers["x-status"]
                        if status == "OK":
                            data = response.content
                            # Yes I know this is horrible, but its a quick fix to issues with tomcat 5.x bugs that have been reported, will find a propper fix laters
                            try:
                                if response.headers["server"].find("Apache-Coyote/1.1") > 0:
                                    data = data[:len(data) - 1]
                            except Exception as e:
                                log.error("[%s:%d] [%s:%s] Reader - Exception - Apache-Coyote/1.1" % (self.target, self.port, self.cookie, self.processid))
                                log.error(e)

                            if data is None:
                                data = ""
                            # log.info("[%s:%d] reader , cookie [%s], processid [%s], retry [%d]" % (self.target, self.port, self.cookie, self.processid, num_retry))
                            break  # finish retry loop
                        elif status == "RETRY":
                            # retry another worker process
                            num_retry += 1
                            headers = {"X-CMD": "READ", "Cookie": self.cookie, "Connection": "Keep-Alive",
                                       "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
                            log.debug("[%s:%d] [%s:%s] Reader - RETRY" % (self.target, self.port, self.cookie, self.processid))
                            continue
                        else:
                            data = None
                            log.error(
                                "[%s:%d] [%s:%s] Reader - Code: %d | Status: [%s] | Message: [%s]" % (
                                    self.target, self.port, self.cookie, self.processid, response.status_code, status,
                                    response.headers["X-ERROR"]))
                            break  # finish retry loop
                    else:
                        log.error("[%s:%d] [%s:%s] Reader - ERROR - Code: %d" % (
                            self.target, self.port, self.cookie, self.processid, response.status_code))
                        break  # finish retry loop

                if data is None:
                    # Remote socket closed
                    log.debug("[%s:%d] [%s:%s] Reader - Data is None" % (self.target, self.port, self.cookie, self.processid))
                    break
                if len(data) == 0:
                    sleep(0.1)
                    continue
                transferLog.info("[%s:%d] [%s:%s] Reader - <<<< [%d] | %r" % (
                    self.target, self.port, self.cookie, self.processid, len(data), data[:30]))
                self.pSocket.send(data)
            except Exception as ex:
                log.error("[%s:%d] [%s:%s] Reader - Exception" % (self.target, self.port, self.cookie, self.processid))
                log.error(ex)

        log.debug("[%s:%d] [%s:%s] Reader - Closing connection" % (
            self.target, self.port, self.cookie, self.processid))
        self.closeRemoteSession()
        try:
            self.pSocket.close()
        except:
            pass

    def writer(self):
        global READBUFSIZE
        global args
        # conn = urllib3.PoolManager()
        headers = {"X-CMD": "FORWARD", "Cookie": str(self.cookie) + ';' + args.cookie, "Connection": "Keep-Alive",
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
        while not self.closed:
            try:
                data_available = False
                socket_list = [self.pSocket]
                read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
                for sock in read_sockets:
                    if sock == self.pSocket:
                        data_available = True
                        break

                if not data_available:
                    time.sleep(0.1)
                    continue

                data = self.pSocket.recv(READBUFSIZE)
                if not data:
                    log.debug("[%s:%d] [%s:%s] Writer - No more data" % (self.target, self.port, self.cookie, self.processid))
                    break
                num_retry = 0
                while num_retry < MAX_RETRY:
                    if DEBUG: log.debug("[+] Try to send data, num_retry = %d" % num_retry)
                    if DEBUG: log.debug(
                        "[+] writer: POST " + self.connectString + "?cmd=forward&processid=" + self.processid + "&sessionid=" + self.cookie)
                    if DEBUG: log.debug("[+] writer: request_headers: " + repr(headers))
                    response = requests.post(
                        self.connectString + "?cmd=forward&processid=" + self.processid + "&sessionid=" + self.cookie,
                        headers=headers, data=merge_two_dicts({'b64data': base64.b64encode(data)}, args.post_data), allow_redirects=False, verify=False, proxies={'http': 'http://localhost:8080'})
                    if DEBUG: log.debug("[+] writer: response.status_code:", response.status_code)
                    if DEBUG: log.debug("[+] writer: response.headers:", response.headers)
                    if response.status_code == 200:
                        status = response.headers["x-status"]
                        if status == "OK":
                            # log.info("[%s:%d] [%s:%s] Writer - Retry: %d" % (
                                # self.target, self.port, self.cookie, self.processid, num_retry))
                            transferLog.info("[%s:%d] [%s:%s] Writer - Retry: %d | >>>> [%d] | %r" % (
                                self.target, self.port, self.cookie, self.processid, num_retry, len(data), data[:30]))
                            break  # finish retry loop
                        elif status == "RETRY":
                            # retry another worker process
                            num_retry += 1
                            headers = {"X-CMD": "FORWARD", "Cookie": self.cookie, "Connection": "Keep-Alive",
                                       "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" + random_useragent()}
                            log.debug("[%s:%d] [%s:%s] Writer - RETRY" % (self.target, self.port, self.cookie, self.processid))
                            continue
                        else:
                            log.error("[%s:%d] [%s:%s] Writer - ERROR - Code: %d | Status: %s | Message: %s" % (
                                self.target, self.port, self.cookie, self.processid, response.status_code, status, response.headers["x-error"]))
                            break  # finish retry loop
                    else:
                        log.error(
                            "[%s:%d] [%s:%s] Writer - ERROR - Code: %d | Data: %s" % (self.target, self.port, self.cookie, self.processid, response.status_code, response.content))
                        break  # finish retry loop
            except timeout:
                log.debug("[%s:%d] [%s:%s] Writer - Timeout" % (self.target, self.port, self.cookie, self.processid))
                continue
            except Exception as ex:
                log.debug("[%s:%d] [%s:%s] Writer - Exception" % (self.target, self.port, self.cookie, self.processid))
                log.error(ex)
                break

        log.debug("[%s:%d] [%s:%s] Writer - Closing connection" % (
            self.target, self.port, self.cookie, self.processid))
        self.closeRemoteSession()
        try:
            self.pSocket.close()
        except:
            pass

    def control_c(self):
        try:
            while True:
                pass
        except KeyboardInterrupt as e:
            os.__exit(0)

    def run(self):
        try:
            if self.handleSocks(self.pSocket):
                # log.debug("Starting reader")
                r = Thread(target=self.reader, args=())
                r.start()
                # log.debug("Starting writer")
                w = Thread(target=self.writer, args=())
                w.start()
                # c = Thread(target=self.control_c, args=())
                # c.start()
                # c.join()
                r.join()
                w.join()
        except SocksCmdNotImplemented, si:
            log.error("SocksCmdNotImplemented")
            self.pSocket.close()
        except SocksProtocolNotImplemented, spi:
            log.error("SocksProtocolNotImplemented")
            self.pSocket.close()
        except BaseException, e:
            log.error("BaseException")
            log.error(e)
            if self.cookie:
                self.closeRemoteSession()
            self.pSocket.close()


def askGeorg(connectString):
    #print 'connectString ', connectString

    r = requests.get(connectString, verify=False)
    #log.info(r.text)
    if r.status_code == 200 and r.text.strip() == BASICCHECKSTRING:
        log.info(r.text)
        return True
    return False


args = None
if __name__ == '__main__':
    print """willem@sensepost.com / @_w_m__
  sam@sensepost.com / @trowalts
  etienne@sensepost.com / @kamp_staaldraad
   """
    log.setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(description='Socks server for reGeorg HTTP(s) tunneller')
    parser.add_argument("-l", "--listen-on", metavar="", help="The default listening address", default="127.0.0.1")
    parser.add_argument("-p", "--listen-port", metavar="", help="The default listening port", type=int, default="8888")
    parser.add_argument("-r", "--read-buff", metavar="", help="Local read buffer, max data to be sent per POST",
                        type=int, default="1024")
    parser.add_argument("-u", "--url", metavar="", required=True, help="The url containing the tunnel script")
    parser.add_argument("-v", "--verbose", metavar="", help="Verbose output[INFO|DEBUG]", default="INFO")
    parser.add_argument("-c", "--cookie", metavar="", default='')
    parser.add_argument("-d", "--post_data", metavar="", default=None)
    parser.add_argument("-t", "--trace", help="Trace the requests/responses", action='store_true')
    args = parser.parse_args()
    if (args.verbose in LEVEL):
        log.setLevel(LEVEL[args.verbose])
        log.info("Log Level set to [%s]" % args.verbose)

    if args.trace:
        DEBUG = True

    if args.post_data is not None:
        post_data = {}
        raw_post_data = args.post_data
        for param in raw_post_data.split('&'):
            key, value = param.split('=')[0], '='.join(param.split('=')[1:])
            post_data[key] = value
        args.post_data = post_data
    else:
        args.post_data = {}

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
            # log.debug("Incomming connection")
            session(sock, args.url).start()
        except KeyboardInterrupt, ex:
            break
        except Exception, e:
            log.error(e)
    servSock.close()

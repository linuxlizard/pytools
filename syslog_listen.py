import sys
import logging
import socket
import threading
import signal
import select
import time

logger = logging.getLogger("syslog_listen")

class ParseError(Exception):
	def __init__(self, errmsg, bad_line):
		super().__init__(errmsg)
		self.bad_line = bad_line

	def __str__(self):
		s = super().__str__()
		# note using 'r' on the string to sanitize the field
		s += "; bad_line={!r:s}".format(self.bad_line)
		return s

class SyslogListener:

	base_mask = select.POLLIN | select.POLLPRI
	error_mask = select.POLLERR | select.POLLHUP | select.POLLNVAL

	def __init__(self, port):
		self.port = port
		self.sock = None
		self.pobj = select.poll()
		self.quit = threading.Event()

		# Create socket to wake up blocking calls on select.poll object
		self.wake_sock_read, self.wake_sock_write = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
		logger.debug("wake_sock read=%d write=%d", self.wake_sock_read.fileno(), self.wake_sock_write.fileno())
		self.pobj.register(self.wake_sock_read, self.base_mask|self.error_mask)

	def start(self):
		logger.info("start")
		self.quit.clear()
		self._connect()

	def _connect(self):
		if self.sock:
			# already connected
			logger.debug("_connect sock=%s already connected", self.sock)
			return

		self.quit.clear()

		logger.debug("%#x connect %d", id(self), self.port)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(('', self.port))
		self.pobj.register(self.sock, self.base_mask|self.error_mask)

	def stop(self):
		#
		# BIG FAT WARNING!!! can be called from signal context or another
		# thread context.
		#
		# so do NOT call logger functions.
		#
		self.quit.set()
		# poke the wake socket to wake up blocks on poll()
		self.wake_sock_write.send(bytes(1))

	def close(self):
		if self.sock is None:
			return
		self.pobj.unregister(self.sock)
		self.sock.close()
		self.sock = None

	def stop(self):
		#
		# BIG FAT WARNING!!! can be called from signal context or another
		# thread context.
		#
		# so do NOT call logger functions.
		#
		self.quit.set()
		# poke the wake socket to wake up blocks on poll()
		self.wake_sock_write.send(bytes(1))

	def wait(self, timeout=None):
		while not self.quit.is_set():
			logger.debug("waiting for messages...")

			pevt_list = self.pobj.poll(timeout)

			if self.quit.is_set():
				break

			if not pevt_list:
				if timeout:
					return None
				logger.error("no events: should not happen!")
				continue

			for pevt in pevt_list:
				logger.debug(pevt)

				fd, mask = pevt

				if mask & self.error_mask:
					logger.error("error fd=%d %#x", fd, mask)
					raise SocketError("fd=%d poll mask=%#x" % (fd, mask))

				if mask & select.POLLIN:
					if fd == self.sock.fileno():
						buf = self.sock.recv(65535)
						# caller's responsibility to decode however they want
						return buf
					elif fd == self.wake_sock_read.fileno():
						# ignore result
						_ = self.wake_sock_read.recv(65535)

	def __run(self):
		while True:
			buf = self.wait()
			logger.debug("recv buf=%r", buf)
			if buf is None:
				# wait returns None on quit or timeout
				return None

			try:
				msg_level, msg = self.parse_message(buf.decode("utf8"))
			except ParseError as err:
				# client threw something at me I don't recognize
				logger.error(err)
				continue
			timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
			logger.info("%s <%d> %s", timestamp, msg_level, msg)

	def parse_message(self, msg):
		# decode an unsolicited message from wpa_supplicant

		# first few chars should be <%d> where %d = single digit integer
		if msg[0] != '<':
			raise ParseError("didn't find <%%d>", msg)

		pos = 1
		try:
			while msg[pos] != '>':
				pos += 1
		except IndexError as err:
			raise ParseError("failed to find closing '>'", msg) from err

		msg_level_str = msg[1:pos]
		try:
			msg_level = int(msg_level_str)
		except ValueError as err:
			raise ParseError("%s is not an integer" % msg_level_str, msg) from err

		# skip over the closing >
		pos += 1

		# rest of line is a free-form message
		msg = msg[pos:].strip()

		return msg_level, msg

	def run(self):
		if not self.sock:
			raise ValueError("connect first")

		self.__run()

if __name__ == '__main__':
	level = logging.INFO
#	level = logging.DEBUG
	logging.basicConfig(level=level)

	port = int(sys.argv[1])
	srv = SyslogListener(port)

	for sig in (signal.SIGTERM, signal.SIGINT):
		signal.signal(sig, lambda signum, stack_frame: srv.stop())

	srv.start()
	srv.run()
	srv.stop()
	srv.close()

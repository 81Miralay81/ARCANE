"""Yerel ağ (LAN) oyunu: oyun bulma (UDP yayın), bağlantı (TCP) ve kilitli adımlı (lockstep) girdi senkronu.

Her iki bilgisayar da aynı oyunu aynı rastgele tohumla çalıştırır; her karede sadece
oyuncuların tuş girdileri gönderilir. Böylece iki ekranda da birebir aynı oyun oynanır.
"""
import json
import queue
import socket
import threading
import time

DISCOVERY_PORT = 47800
GAME_PORT = 47801
MAGIC = "KANATIX1"
INPUT_DELAY = 3          # kare: ağ gecikmesini gizlemek için girdiler 3 kare sonra uygulanır


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


class Announcer:
    """Kurucu: ağda varlığını duyurur."""

    def __init__(self, mode, name):
        self.mode, self.name = mode, name
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = f"{MAGIC}|{self.mode}|{self.name}|{GAME_PORT}".encode("utf-8")
        ip = local_ip()
        subnet = ".".join(ip.split(".")[:3]) + ".255" if ip.count(".") == 3 else "255.255.255.255"
        while self.running:
            for addr in ("255.255.255.255", subnet, "<broadcast>"):
                try:
                    s.sendto(msg, (addr, DISCOVERY_PORT))
                except Exception:
                    pass
            time.sleep(0.6)
        s.close()

    def stop(self):
        self.running = False


class Finder:
    """Katılan: ağdaki oyunları dinler."""

    def __init__(self):
        self.hosts = {}       # ip -> (mode, name, port, son görülme)
        self.running = True
        self.error = None
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", DISCOVERY_PORT))
            s.settimeout(0.5)
        except Exception as e:
            self.error = str(e)
            return
        while self.running:
            try:
                data, (ip, _) = s.recvfrom(512)
                parts = data.decode("utf-8", "ignore").split("|")
                if len(parts) == 4 and parts[0] == MAGIC:
                    self.hosts[ip] = (parts[1], parts[2], int(parts[3]), time.time())
            except socket.timeout:
                pass
            except Exception:
                pass
        s.close()

    def list(self):
        now = time.time()
        return [(ip, *v[:3]) for ip, v in sorted(self.hosts.items()) if now - v[3] < 3.0]

    def stop(self):
        self.running = False


class Connection:
    """Satır bazlı JSON mesajları taşıyan TCP bağlantısı."""

    def __init__(self, sock):
        self.sock = sock
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(None)
        self.inbox = queue.Queue()
        self.alive = True
        self.lock = threading.Lock()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        buf = b""
        try:
            while self.alive:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line:
                        try:
                            self.inbox.put(json.loads(line.decode("utf-8")))
                        except Exception:
                            pass
        except Exception:
            pass
        self.alive = False

    def send(self, obj):
        if not self.alive:
            return
        try:
            data = (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")
            with self.lock:
                self.sock.sendall(data)
        except Exception:
            self.alive = False

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.inbox.get_nowait())
            except queue.Empty:
                return out

    def close(self):
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class HostListener:
    """Kurucu: katılanı TCP ile bekler."""

    def __init__(self):
        self.conn = None
        self.error = None
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("", GAME_PORT))
            srv.listen(1)
            srv.settimeout(0.5)
        except Exception as e:
            self.error = f"Port {GAME_PORT} açılamadı: {e}"
            return
        while self.running and self.conn is None:
            try:
                s, _ = srv.accept()
                self.conn = Connection(s)
            except socket.timeout:
                pass
            except Exception as e:
                self.error = str(e)
                break
        srv.close()

    def stop(self):
        self.running = False


def connect(ip, port=GAME_PORT, timeout=4.0):
    s = socket.create_connection((ip, port), timeout=timeout)
    return Connection(s)


class Lockstep:
    """Kare kare girdi değişimi. local_side: 0 = kurucu, 1 = katılan."""

    def __init__(self, conn, local_side, seed=0, round_no=0):
        self.conn = conn
        self.side = local_side
        self.seed = seed
        self.round = round_no
        self.frame = 0
        self.inputs = [{}, {}]           # kare -> girdi
        for f in range(INPUT_DELAY):
            self.inputs[0][f] = None
            self.inputs[1][f] = None
        self.sent_upto = INPUT_DELAY - 1
        self.disconnected = False
        self.remote_msgs = []
        self.wait_time = 0.0
        self.checks = {}
        self.early = []

    def push_local(self, inp):
        """Yerel girdiyi INPUT_DELAY kare sonrası için kaydet ve gönder."""
        f = self.frame + INPUT_DELAY
        if f <= self.sent_upto:
            return
        self.inputs[self.side][f] = inp
        self.sent_upto = f
        self.conn.send({"t": "in", "r": self.round, "f": f, "i": inp})

    def pump(self):
        for m in self.conn.poll():
            t = m.get("t")
            if t == "in":
                if m.get("r", 0) == self.round:
                    self.inputs[1 - self.side][m["f"]] = m["i"]
                elif m.get("r", 0) > self.round:
                    self.early.append(m)
            elif t == "chk":
                if m.get("r", 0) == self.round:
                    self.checks.setdefault(m["f"], [None, None])[1 - self.side] = m["v"]
            else:
                self.remote_msgs.append(m)
        if not self.conn.alive:
            self.disconnected = True

    def ready(self):
        return self.frame in self.inputs[0] and self.frame in self.inputs[1]

    def take(self):
        """Bu karenin iki girdisini döndürüp kareyi ilerletir."""
        a = self.inputs[0].pop(self.frame)
        b = self.inputs[1].pop(self.frame)
        self.frame += 1
        return a, b

    def checksum(self, value):
        """Her iki tarafın simülasyonu aynı mı? (her 120 karede bir)"""
        f = self.frame
        if f % 120 == 0:
            self.checks.setdefault(f, [None, None])[self.side] = value
            self.conn.send({"t": "chk", "r": self.round, "f": f, "v": value})

    def desynced(self):
        for f, (a, b) in list(self.checks.items()):
            if a is not None and b is not None:
                del self.checks[f]
                if a != b:
                    return True
        return False

    def restart(self):
        """Aynı bağlantıyla yeni tur (rövanş / tekrar dene)."""
        nxt = Lockstep(self.conn, self.side, self.seed, self.round + 1)
        for m in self.early:
            if m.get("r") == nxt.round:
                nxt.inputs[1 - nxt.side][m["f"]] = m["i"]
        return nxt

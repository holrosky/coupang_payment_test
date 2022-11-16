import requests
from random import randint
import tempfile
import subprocess
import base64
import time
import psutil

class IPManager:
    def __init__(self):
        self.original_ip = self.get_ip()
        self.ip_proc = None

    def get_ip(self):
        return requests.get("https://api.ipify.org").text

    def disconnect(self):
        for proc in psutil.process_iter():
            if "openvpn.exe" == proc.name():
                proc.kill()
                break

    def change_ip(self):
        country = 'korea'

        self.disconnect()

        time.sleep(5)

        while self.original_ip == self.get_ip():
            waiting_sec = 10

            try:
                vpn_data = requests.get("http://www.vpngate.net/api/iphone/").text.replace("\r", "")
                servers = [line.split(",") for line in vpn_data.split("\n")]
                labels = servers[1]
                labels[0] = labels[0][1:]
                servers = [s for s in servers[2:] if len(s) > 1]
            except BaseException:
                print("Cannot get VPN servers data")

            desired = [s for s in servers if country.lower() in s[5].lower()]
            found = len(desired)
            print("Found " + str(found) + " servers for country " + country)
            if found == 0:
                print('사용 가능한 IP가 없습니다. 잠시 후 다시 실행해 주세요.')
                exit(1)

            supported = [s for s in desired if len(s[-1]) > 0]
            print(str(len(supported)) + " of these servers support OpenVPN")

            winner = sorted(supported, key=lambda s: float(s[2].replace(",", ".")), reverse=True)[
                randint(0, len(supported) - 1)]

            print("\n== Connect server Info ==")
            pairs = list(zip(labels, winner))[:-1]

            for (l, d) in pairs[:4]:
                print(l + ": " + d)
            print(pairs[4][0] + ": " + str(float(pairs[4][1]) / 10 ** 6) + " MBps")
            print("Country: " + pairs[5][1])

            print("\nLaunching VPN...")
            _, path = tempfile.mkstemp()

            f = open(path, "w")
            f.write(base64.b64decode(winner[-1]).decode())
            self.ip_proc = subprocess.Popen(["openvpn", "--config", path])

            while self.original_ip == self.get_ip():
                time.sleep(1)
                if waiting_sec > 0:
                    waiting_sec -= 1
                else:
                    print('retry!')
                    self.disconnect()
                    break
import random
from collections import deque, defaultdict
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import requests
import ipaddress
from bs4 import BeautifulSoup
import httpx


def valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def from_free_proxy_cz():
    try:
        url = "http://free-proxy.cz/en/"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        scripts = soup.find_all("script", type="text/javascript")
        proxies = set()

        for script in scripts:
            if 'document.write' in script.text:
                ip = script.text.split('("')[1].split('")')[0]
                port = script.find_next_sibling("span").text
                proxies.add(f"{ip}:{port}")
        return proxies
    except Exception as e:
        print(f"Ошибка free-proxy.cz: {e}")
        return set()


def parse_ssl_table(url):
    proxies = set()
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                ip, port = cols[0].text.strip(), cols[1].text.strip()
                if valid_ip(ip):
                    proxies.add(f"{ip}:{port}")
    except Exception as e:
        print(f"Ошибка SSL-таблицы: {e}")
    return proxies


def from_htmlweb_api():
    try:
        url = "http://htmlweb.ru/json/proxy/get?short=4&type=HTTP"
        resp = requests.get(url, timeout=15)
        return set(resp.text.splitlines())
    except Exception as e:
        print(f"Ошибка htmlweb API: {e}")
        return set()


def from_proxycompass():
    try:
        url = "https://proxycompass.com/free-proxy/"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        return {f"{row.select_one('td:nth-child(1)').text}:{row.select_one('td:nth-child(2)').text}"
                for row in soup.select("table tr")[1:21]}
    except Exception as e:
        print(f"Ошибка proxycompass: {e}")
        return set()


def from_spys_one():
    try:
        url = "https://spys.one/en/free-proxy-list/"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        proxies = set()

        for row in soup.select("tr[onmouseover]"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                ip_script = cols[0].script
                if ip_script:
                    ip = ip_script.text.split("(")[-1].split(")")[0].replace("'+'", "")
                port = cols[0].font.text.strip()
                proxies.add(f"{ip}:{port}")
        return proxies
    except Exception as e:
        print(f"Ошибка spys.one: {e}")
        return set()


def from_geonode():
    try:
        url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1"
        r = requests.get(url, timeout=10)
        return {f"{item['ip']}:{item['port']}" for item in r.json()['data']}
    except Exception as e:
        print(f"Ошибка geonode: {e}")
        return set()


def from_proxy_list_download():
    try:
        url = "https://www.proxy-list.download/api/v1/get?type=http"
        r = requests.get(url, timeout=10)
        return set(r.text.strip().splitlines())
    except Exception as e:
        print(f"Ошибка proxy-list.download: {e}")
        return set()


def from_sslproxies():
    return parse_ssl_table("https://sslproxies.org")


def from_free_proxy_list():
    return parse_ssl_table("https://free-proxy-list.net")


def check_proxy(proxy):
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    test_url = "https://www.cian.ru/rent/"  # легкий раздел ЦИАН, не вызывает капчу

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        response = requests.get(test_url, proxies=proxies, headers=headers, timeout=7)


        return proxy
    except Exception as e:
        return None


def fetch_all_proxies():
    sources = [
        from_proxy_list_download,
        from_sslproxies,
        from_free_proxy_list,
        from_geonode,
        from_spys_one,
        from_proxycompass,
        from_htmlweb_api,
        from_free_proxy_cz
    ]
    proxies = set()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda src: src(), sources)
        for result in results:
            proxies.update(result)
    return list(proxies)


class ProxyManager:
    def __init__(self, use_local_ratio: float = 0.2):
        self.proxies_queue = deque()
        self.lock = Lock()
        self.proxy_errors = defaultdict(int)
        self.max_errors = 3
        self.use_local_ratio = use_local_ratio

    def init(self):
        print("Инициализация прокси...")
        raw_proxies = fetch_all_proxies()
        with ThreadPoolExecutor(max_workers=50) as executor:
            valid_proxies = list(executor.map(check_proxy, raw_proxies))
        valid_proxies = [p for p in valid_proxies if p]
        print(f"Рабочих прокси: {len(valid_proxies)}")
        self.proxies_queue.clear()
        self.proxies_queue.extend(valid_proxies)

    def get_proxy(self):
        with self.lock:
            if not self.proxies_queue:
                print("Прокси закончились. Повторная инициализация...")
                self.init()
            proxy = self.proxies_queue.popleft()
            self.proxies_queue.append(proxy)
            return proxy

    def report_error(self, proxy):
        with self.lock:
            self.proxy_errors[proxy] += 1
            if self.proxy_errors[proxy] >= self.max_errors:
                try:
                    self.proxies_queue.remove(proxy)
                    print(f"[ProxyManager] Удалён прокси: {proxy} после {self.max_errors} ошибок")
                except ValueError:
                    pass

    def get_httpx_client(self):
        use_local = random.random() < self.use_local_ratio

        if use_local:
            print("[ProxyManager] Используем локальный IP")
            client = httpx.AsyncClient(timeout=15.0)
            return client, "LOCAL"

        proxy = self.get_proxy()
        print(f"[ProxyManager] Используем прокси: {proxy}")
        client = httpx.AsyncClient(
            proxy="http://" + proxy,
            timeout=15.0
        )
        return client, proxy
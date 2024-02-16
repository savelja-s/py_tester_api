from typing import Union
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urlparse


class BenchmarkTester:
    def __init__(self, _api_host: str, urls_file_path: str, _concurrency=1):
        self.api_host = _api_host
        self.api_port = self.extract_port(_api_host)
        self.urls = self.load_config(urls_file_path)
        self.urls_count = len(self.urls)
        self.concurrency = _concurrency
        self.total_requests = self.urls_count * self.concurrency
        self.lock = threading.Lock()
        self.total_time = 0
        self.start_time = 0
        self.successful_requests = 0
        self.log_file_path = f'logs/benchmark_log_{time.strftime("%Y%m%d_%H%M%S")}.log'

    @staticmethod
    def load_config(_config_file_path: str):
        with open(_config_file_path, 'r') as config_file:
            return json.load(config_file)

    def make_request(self, url, method='GET', query=None, payload=None, _bearer_token=None):
        headers = {'Content-Type': 'application/json'}

        if _bearer_token:
            headers['Authorization'] = f'Bearer {_bearer_token}'

        start_time = time.time()

        try:
            if method == 'GET':
                response = requests.get(url, params=query, headers=headers)
            elif method == 'POST':
                response = requests.post(url, params=query, data=json.dumps(payload), headers=headers)
            elif method == 'PUT':
                response = requests.put(url, params=query, data=json.dumps(payload), headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, params=query, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response_time = time.time() - start_time
            self.log_request(
                f"{method} request to {url}", f"Headers: {headers}", f"Payload: {payload}",
                f"Response with status: {response.status_code}", f"Headers: {response.headers}",
                f"Body: {response.text}"
            )

            return response_time, response.status_code, response
        except requests.exceptions.RequestException as e:
            return 0, 0, 0

    def log_request(self, *messages):
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(f"\n--- {time.ctime()} ---\n")
            for message in messages:
                log_file.write(f"{message}\n")

    def prepare_url(self, url: str) -> str:
        return f'{self.api_host}{"" if url.startswith("/") else "/"}{url}'

    @staticmethod
    def extract_port(url: str) -> Union[int, None]:
        parsed_url = urlparse(url)
        if parsed_url.port is not None:
            return parsed_url.port
        elif parsed_url.scheme == 'http':
            return 80
        elif parsed_url.scheme == 'https':
            return 443
        else:
            return None

    def run_test_for_user(self, _bearer_token=None) -> None:
        local_total_time = 0
        local_successful_requests = 0

        for entry in self.urls:
            url = self.prepare_url(entry.get('url'))
            method = entry.get('method', 'GET').upper()
            query = entry.get('query', None)
            body = entry.get('body', None)

            response_time, status_code, response = self.make_request(url, method, query, body, _bearer_token)
            local_total_time += response_time

            if 200 <= status_code < 210:
                local_successful_requests += 1

        with self.lock:
            self.total_time += local_total_time
            self.successful_requests += local_successful_requests

    def run_test(self, _bearer_token=None):
        self.start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = []

            for user_index in range(self.concurrency):
                futures.append(executor.submit(self.run_test_for_user, _bearer_token))

            for future in as_completed(futures):
                future.result()
        elapsed_time = time.time() - self.start_time
        self.print_stats(elapsed_time)

    def print_stats(self, elapsed_time: float):
        with self.lock:
            print("\nServer Software:")
            print(f"Server Hostname:     {self.api_host}")
            print(f"Server Port:         {self.api_port}")
            print("Elapsed Time:         {:.3f} seconds".format(elapsed_time))
            print("\nConcurrency Level:  {}".format(self.concurrency))
            print("Time taken for tests: {:.3f} seconds".format(self.total_time))
            print(f"Total requests:      {self.total_requests}")
            print(f'Failed requests:     {(self.total_requests - self.successful_requests)}')
            print("Total transferred:    {} bytes".format(self.total_time))
            if self.total_time:
                print("Requests per second:  {:.2f} [#/sec] (mean)".format(self.total_requests / self.total_time))
                print("Time per request:     {:.3f} [ms] (mean)".format((self.total_time / self.total_requests) * 1000))
                print("Time per request(OU): {:.3f} [ms] (mean)".format(self.total_time / self.concurrency * 1000))

            with open(self.log_file_path, 'a') as log_file:
                log_file.write("\n\n")
                log_file.write(f"Server Hostname:        {self.api_host}\n")
                log_file.write(f"Server Port:            {self.api_port}\n")
                log_file.write("Elapsed Time:           {:.3f} seconds".format(elapsed_time))
                log_file.write("\nConcurrency Level:      {}".format(self.concurrency))
                log_file.write("\nTime taken for tests:   {:.3f} seconds".format(self.total_time))
                log_file.write(f"\nTotal requests:         {self.total_requests}\n")
                log_file.write(f'Failed requests:        {(self.total_requests - self.successful_requests)}\n')
                log_file.write("Total transferred:      {} bytes".format(self.total_time))
                if self.total_time:
                    log_file.write("\nRequests per sec:   {:.2f} [#/sec]".format(self.total_requests / self.total_time))
                    log_file.write(
                        "\nTime per request:        {:.3f} [ms]".format((self.total_time / self.total_requests) * 1000))
                    log_file.write(
                        "\nTime per request(OU):         {:.3f} [ms]".format(self.total_time / self.concurrency * 1000))

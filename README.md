# py_tester_api
#Install packages
```bash
sudo apt install -y python3.10-dev python3.10-venv python3-setuptools
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#Example url file
```json
[
    {
        "url": "https://api.example.com/data",
        "method": "GET",
        "query": {"param1": "value1"}
    },
    {
        "url": "https://api.example.com/other",
        "method": "POST",
        "query": {"param2": "value2"},
        "body": {"key": "value"}
    },
    {
        "url": "https://api.example.com/something",
        "method": "PUT",
        "body": {"data": "example"}
    }
]
```
##Example use code 
```python
from main import BenchmarkTester

if __name__ == "__main__":
    config_file_path: str = 'urls-example.json'
    api_host: str = 'https://api.example.com'
    concurrency: int = 12
    # bearer_token = None
    bearer_token = 'some token'

    tester = BenchmarkTester(api_host, config_file_path, concurrency)
    tester.run_test(bearer_token)
```
##Example use code 2
```python
from main import BenchmarkTester

class MyClass(BenchmarkTester):
    def run_test_for_user(self, _bearer_token=None):
        # New logic
        pass


if __name__ == "__main__":
    config_file_path = 'urls-example.json'
    api_host = 'https://api.example.com'
    concurrency = 12
    # bearer_token = None
    bearer_token = 'some token'

    tester = MyClass(api_host, config_file_path, concurrency)
    tester.run_test(bearer_token)
```
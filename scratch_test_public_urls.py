import requests

urls = [
    "https://dorocaviar-storage.b-cdn.net/test_connection.txt",
    "https://dorocaviar-storage.b-cdn.net/dorocaviar-storage/test_connection.txt",
    "https://dorocaviar-storage.b-cdn.net/videos/1005037594.mp4",
    "https://dorocaviar-storage.b-cdn.net/dorocaviar-storage/videos/1005037594.mp4",
    "https://storage.bunnycdn.com/dorocaviar-storage/test_connection.txt",
]

for url in urls:
    try:
        r = requests.head(url, timeout=10)
        print(f"HEAD {url} -> Status: {r.status_code}")
        if r.status_code == 200:
            print("  SUCCESS!")
    except Exception as e:
        print(f"ERROR {url}: {e}")

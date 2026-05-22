import requests
import json

headers = {
    'AccessKey': 'e0ca0efa-1c04-408b-ba89a46b2fdb-e32f-4696'
}

print("Fetching file list from Bunny Storage...")
response = requests.get('https://storage.bunnycdn.com/dorocaviar-storage/', headers=headers)
print("HTTP Status Code:", response.status_code)

if response.status_code == 200:
    files = response.json()
    print(f"Found {len(files)} items in storage zone.")
    for f in files[:20]:
        print(f"- {f.get('ObjectName')} ({f.get('Length')} bytes, IsDirectory: {f.get('IsDirectory')})")
        if f.get('ObjectName') == 'videos':
            print("  Listing videos directory...")
            v_resp = requests.get('https://storage.bunnycdn.com/dorocaviar-storage/videos/', headers=headers)
            if v_resp.status_code == 200:
                v_files = v_resp.json()
                for vf in v_files[:10]:
                    print(f"    * {vf.get('ObjectName')} ({vf.get('Length')} bytes)")
else:
    print("Error text:", response.text)

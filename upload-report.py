import requests
import os

headers = {
    'Authorization': f'Token {os.environ["DEFECTDOJO_API_KEY"]}'
}

url = 'https://demo.defectdojo.org/v2/import-scan/'

data = {
    'active': True,
    'varified': True,
    'scan_type': 'Gitleaks Scan',
    'minimum_severity': 'low',
    'engagement': 4
}

files = {
    'file': open('gitleaks.json', 'rb')
}

response = requests.post(url, headers=headers, data=data, files=files)

if response.status_code ==201:
    print('scan results imported successfully')
else:
    print(f'failed to import scan results: {response.content}')    

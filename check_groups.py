import requests

api_key = "0XB72928E8F989B66EF693CD31E699DC49DFBC14F486021F2A7C9A6D8185E9151EF9F42884A5D149C7BA06F0AE8F93F415"
url = "https://api.activetrail.com/v1/groups"
headers = {"Authorization": api_key}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        groups = response.json()
        for group in groups:
            print(f"ID: {group['id']} - Name: {group['name']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")

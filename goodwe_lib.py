import requests
import json

# Do not run the code without the inversor file created
# {"GoodWeLogin": "", "GoodWePass": "", "station_id": ""}
with open("good_we_data.json", "r") as good_we_data:
  good_we_data_js = json.loads(good_we_data.read())
  good_we_data.close()

def return_goodwe_reading():
    # Login into the website API
    url = 'https://www.semsportal.com/api/v2/Common/CrossLogin'
    payload = {"account":good_we_data_js["GoodWeLogin"],"pwd": good_we_data_js["GoodWePass"]}# If you need to test the code,, please ask us the account and password
    headers = {'content-type': 'application/json', 'Connect': 'keep-alive', 'User-Agent': 'PVMaster/2.1.0 (iPhone; iOS 13.0; Scale/2.00)', 'Accept-Language': 'en;q=1', 'Token': '{"version":"v2.1.0","client":"ios","language":"en"}' }
    r = requests.post(url, data=str(payload), headers=headers)
    login = r.json()

    # request the API info about the energy produced by the power inverters
    url = 'https://www.semsportal.com/api/v2/PowerStation/GetMonitorDetailByPowerstationId'
    payload = {"powerStationId": good_we_data_js["station_id"]}
    headers = {'Content-Type': 'application/json', 'Accept': '*/*', 'User-Agent': 'PVMaster/2.1.0 (iPhone; iOS 13.0; Scale/2.00)', 'Accept-Language': 'DE;q=1', 'Token': json.dumps(login["data"])}
    r = requests.post(url, data=str(payload), headers=headers)
    PowerSt = r.json()

    return PowerSt
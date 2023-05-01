import base64
import hashlib
import json
import time
import datetime
import hmac
import asyncio
import aiohttp
from typing import Dict

# Do not run the code without the inversor file created
"""{"KeyID" : "1300386381676780676",
    "KeySecret" : "39337525106f4546ab897ac2e9d4d79f"
    }
"""
with open("solis_data.json", "r") as solis_data:
  solis_data_js = json.loads(solis_data.read())
  solis_data.close()

VERB = "POST"

API_URL = "https://www.soliscloud.com:13333"
base = "/v1/api/"
operation = "stationDetailList"
canonicalized_resource = f"{base}{operation}"

def get_date():
        from datetime import datetime, timezone

        # current date and time
        now = datetime.now(timezone.utc)

        t = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        # mm/dd/YY H:M:S format
        return t

def prepare_header(
        key_id: str,
        secret: bytes,
        body: Dict[str, str],
        canonicalized_resource: str
    ) -> dict:
        content_md5 = base64.b64encode(
            hashlib.md5(json.dumps(body, separators=(",", ":")).encode('utf-8')).digest()
        ).decode('utf-8')
        content_type = "application/json" 
        #ts = time.time()
        date = get_date()
        #date = 'Fri, 26 Jul 2019 06:00:46 GMT'
        #date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%d-%m')
        #date = SoliscloudAPI._now().strftime("%a, %d %b %Y %H:%M:%S GMT")

        encrypt_str = (VERB + "\n" +
            content_md5 + "\n" +
            content_type + "\n" +
            date + "\n" +
            canonicalized_resource
        )
        hmac_obj = hmac.new(
            secret,
            msg=encrypt_str.encode('utf-8'),
            digestmod=hashlib.sha1
        )
        hashlib.sha1()
        sign = base64.b64encode(hmac_obj.digest())
        authorization = "API " + key_id + ":" + sign.decode('utf-8')

        header: dict = {
            "Content-MD5": content_md5,
            "Content-Type": content_type,
            "Date": date,
            "Authorization": authorization
        }
        return header

params: Dict[str, str] = {'pageNo': 1, 'pageSize': 10}


url = f"{API_URL}{canonicalized_resource}"

async def run_request():
        header: Dict[str, str] = prepare_header(solis_data_js["KeyID"], bytes(solis_data_js["KeySecret"], 'utf-8'), params, canonicalized_resource)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params, headers=header) as response:
                response = await response.text()
                try:
                    response_json = json.loads(response)
                except json.JSONDecodeError as e:
                    print(response)
                    print("Error decoding JSON:", e)
                    response_json = {}
                #["data"]["records"][0]["allEnergy"]
                return response_json

def return_reading():
    response = asyncio.run(run_request())
    if 'data' in response and 'records' in response["data"]:
        return response["data"]["records"], "allEnergy1"
    else:
        print(response)
        return [], "allEnergy1"

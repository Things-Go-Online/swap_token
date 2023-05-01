import json
import asyncio
import websockets
from decimal import Decimal

WS_URL = "wss://rippled.thingsgo.online:6005"

async def send_transaction(transaction, WS_URL):
    async with websockets.connect(WS_URL) as websocket:
        await websocket.send(transaction)
        response = await websocket.recv()
        return json.loads(response)

def check_price(send_data_js, WS_URL):
    request = {
        "taker_gets": {
            "currency": send_data_js["AMOUNT_CURRENCY"],
            "issuer": send_data_js["AMOUNT_ISSUER"]
            },
        "taker_pays": {
            "currency": send_data_js["SEND_CURRENCY"],
            "issuer": send_data_js["SEND_ISSUER"]
            },
        "limit": 1,
        "id": 4,
        "command": "book_offers"
        }

    result = asyncio.run(send_transaction(json.dumps(request), WS_URL))
    price = 0
    if (("status" in result) and (result["status"] == "success")):
        if(("result" in result) and ("offers" in result["result"])):
            if(len(result["result"]["offers"]) != 0):
                total = result["result"]["offers"][0]["TakerGets"]["value"] #The total price for the amount offered
                volume = result["result"]["offers"][0]["TakerPays"]["value"] #The total amount offered
                price = Decimal(total)/Decimal(volume)
                return price
            else:
                print("There is no offer available")
                return price
        else:
            print("Could not load offers!")
            return price
    else:
        print("Status: " + str(result["status"]))
        return price

def check_status_transaction(tx_hash, WS_URL):
    transaction = { "id": 1, "command": "tx", "transaction": tx_hash, "binary": False }
    response = asyncio.run(send_transaction(json.dumps(transaction), WS_URL))
    return response

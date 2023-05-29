import json
import time
import datetime
from swap_token import send_transaction
import csv
from decimal import Decimal
from goodwe_lib import return_reading
#from solis_lib import return_reading
from check_book_offer import check_status_transaction

with open("send_data.json", "r") as send_data:
    send_data_js = json.loads(send_data.read())
    send_data.close()

WS_URL = "wss://rippled.thingsgo.online:6005"
#WS_URL = "ws://localhost:6006"
etotal_inv_ant = {}
etotal_inv = {}
deltaE_inv = {}
firstrun = 1

try:
  with open('lastenergy.json', 'r+', encoding='utf-8') as f:
    try:
      filejson = json.load(f)
      list_inv = filejson.keys()
      for key in list_inv:
        etotal_inv_ant[key] = filejson[key]
        print("Reading from json file: %s <%s>" % (key, etotal_inv_ant[key]))
        if (etotal_inv_ant[key] >= 0):
            firstrun = 0
    except ValueError:
      print('Decoding JSON has failed')
except:
  with open('lastenergy.json', 'w', encoding='utf-8') as f:
    #filejson = {'etotal_inv01_ant':0}
    #json.dump(filejson, f, ensure_ascii=True, indent=4)
    f.close

def loads_inv_value(etotal_inv, deltaE, tx_hash):
    global etotal_inv_ant
    print(tx_hash)
    time.sleep(10)
    a = check_status_transaction(tx_hash, "wss://rippled.thingsgo.online:6005")
    print(a)
    try:
      for i in range(len(a["result"]["meta"]["AffectedNodes"])):
        node = a["result"]["meta"]["AffectedNodes"][i]["ModifiedNode"]
        if "HighLimit" in node["FinalFields"]:
          if ((node["FinalFields"]["HighLimit"]["issuer"] ==  send_data_js["SEND_ISSUER"]) and (node["FinalFields"]["HighLimit"]["currency"] ==  send_data_js["SEND_CURRENCY"])):
            send_token = Decimal(node["PreviousFields"]["Balance"]["value"]) - Decimal(node["FinalFields"]["Balance"]["value"])
            #print(send_token)
          if ((node["FinalFields"]["HighLimit"]["issuer"] ==  send_data_js["AMOUNT_ISSUER"]) and (node["FinalFields"]["HighLimit"]["currency"] ==  send_data_js["AMOUNT_CURRENCY"])):
            amount_token = Decimal(node["FinalFields"]["Balance"]["value"]) - Decimal(node["PreviousFields"]["Balance"]["value"])
            #print(amount_token)
    except:
      time.sleep(10)
      a = check_status_transaction(tx_hash, "wss://rippled.thingsgo.online:6005")
      for i in range(len(a["result"]["meta"]["AffectedNodes"])):
        node = a["result"]["meta"]["AffectedNodes"][i]["ModifiedNode"]
        if "HighLimit" in node["FinalFields"]:
          if ((node["FinalFields"]["HighLimit"]["issuer"] ==  send_data_js["SEND_ISSUER"]) and (node["FinalFields"]["HighLimit"]["currency"] ==  send_data_js["SEND_CURRENCY"])):
            send_token = Decimal(node["PreviousFields"]["Balance"]["value"]) - Decimal(node["FinalFields"]["Balance"]["value"])
            #print(send_token)
          if ((node["FinalFields"]["HighLimit"]["issuer"] ==  send_data_js["AMOUNT_ISSUER"]) and (node["FinalFields"]["HighLimit"]["currency"] ==  send_data_js["AMOUNT_CURRENCY"])):
            amount_token = Decimal(node["FinalFields"]["Balance"]["value"]) - Decimal(node["PreviousFields"]["Balance"]["value"])

    ts = time.time()
    for inv in etotal_inv.keys():
      inv_ant_name = inv + "_ant"
      etotal_inv_ant[inv_ant_name] =  etotal_inv[inv]
    filejson = etotal_inv_ant
    try:
      with open('lastenergy.json', 'w+', encoding='utf-8') as f:
        json.dump(filejson, f, ensure_ascii=True, indent=4)
    except ValueError:
      with open('lastenergy.json', 'w', encoding='utf-8') as f:
        json.dump(filejson, f, ensure_ascii=True, indent=4)
    try:
      with open('history_registry.json', 'a', encoding='utf-8') as csvf:
        history_writer = csv.writer(csvf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        history_writer.writerow([datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), tx_hash, deltaE, "S", send_token, amount_token])
    except ValueError:
      print('Error openning the history_registry file')

while 1:
    PowerSt, param = return_reading()
    for i in range(len(PowerSt)):
      inv_ant_name = "etotal_inv%s_ant" % (i+1)
      inv_name = "etotal_inv%s" % (i+1)
      etotal_inv[inv_name] = PowerSt[i][param]
      print("Read inverter:" + str(etotal_inv[inv_name]))
      
      if (firstrun and (etotal_inv[inv_name] >= 0)):
        etotal_inv_ant[inv_ant_name] = etotal_inv[inv_name]

      if (etotal_inv_ant[inv_ant_name]>=0):
        deltaE_inv[i] = Decimal(etotal_inv[inv_name] - etotal_inv_ant[inv_ant_name])
      else:
        deltaE_inv[i] = 0

    firstrun = 0
    deltaE = 0 
    totalE = 0 

    for i in range(len(deltaE_inv)):
      deltaE = deltaE + deltaE_inv[i]
      deltaE_inv[i] = 0
    print("DeltaE: " + str(deltaE))

    for i in etotal_inv.values():
      totalE = totalE + i
    print("TotalE: " + str(totalE))

    if deltaE>0:
      response, tx_hash = send_transaction(deltaE, totalE, WS_URL)
      if response == "tesSUCCESS":
        loads_inv_value(etotal_inv, deltaE, tx_hash)
      elif ((response == "terINSUF_FEE_B") or (response == "tecINSUFF_FEE") or (response == "tecINSUFFICIENT_FUNDS")):
        pass
      elif (response == None):
        pass
      else:
        response, tx_hash = send_transaction(deltaE, totalE, WS_URL)
        if response == "tesSUCCESS":
          loads_inv_value(etotal_inv, deltaE, tx_hash)
        else:
          #Energy produced is gonna be added to the next transaction
          pass
      
    time.sleep(60)

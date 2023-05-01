# TGO Swap lib for reading from Power Inverters
Routine for reading energy generation data from power inverters and swap the equivalent value of device-tokens (KHW, for instance) by the TGO Reward Token.

## Usage

### Solis Power Inverter
Create a json configuration file named solis_data.json with the Key ID and the Key secret of the solar power station. You must have an account in the cloud plataform of the power inverter manufacturer (https://www.soliscloud.com). By default, the API is not available at soliscloud. To get it you must send an e-mail to the support of solis' support team.
```yaml
{"KeyID" : "",
    "KeySecret" : ""
    }
```
A sample file is provided, named solis_data.json-sample. Rename it by removing the trailing string "-sample", and edit it with the proper data.

Uncomment the import of the solis_lib and comment the other one at request_inverter.py file
```python
#from goodwe_lib import return_reading
from solis_lib import return_reading
```

### GoodWe Power Inverter
Create a json configuration file named good_we_data.json with the login, password and the ID of the station:
```yaml
{
    "GoodWeLogin": "", 
    "GoodWePass": "", 
    "station_id": ""
}
```

Uncomment the import of the goodwe_lib and comment the other one at request_inverter.py file
```python
from goodwe_lib import return_reading
#from solis_lib import return_reading
```

### Configure some data for the XRP Ledger Cross-currency Payment transaction
Create a json file named send_data.json with the following data:
```yaml
{
    "SENDER_ADDRESS": "", 
    "SENDER_SECRET": "", 
    "FEE": "20", 
    "DESTINATION" : "", 
    "AMOUNT_CURRENCY" : "", 
    "AMOUNT_issuer" : "", 
    "SEND_CURRENCY" : "", 
    "SEND_ISSUER" : ""
}
```
A sample file is provided, named send_data.json-sample. Rename it by removing the trailing string "-sample", and edit it with the proper data.


### lastenergy.json file initial boot
The lasenergy.json file format is:
```yaml
{
"etotal_inv1_ant": numeric_value
}
```

There are three options to configure the initial lastenergy.json file

1- A numeric value (float or integer) greater or equal to "0" (zero)
    If etotal_inv1_ant is greater or equal to "0", the code calculates the delta_energy as the difference from the total energy queried from the solar power inverter API and the etotal_inv1_ant value from the lastenergy.json file. This delta_energy quantity is registered in the XRP Ledger blockchain as a device-token named KWH, for instnace, using a cross-currency payment transaction that swaps automatically this amount of device-token for TGO Reward Token. For instance, if it reads 1230 kWh as the total energy produced by the power inverter since it started to generate electricity and the lasenergy.json etotal_inv1_ant value is "0" (zero), it calculates the delta_energy as: delta_energy = (1230 - 0) = 1230. So, be carefull when setting the initial (first time running) value of the key etotal_inv1_ant of the lastenergy.json file.

2- A negative value
    If etotal_inv1_ant is a negative number (ex: -1), the code will query the API to get the total energy produced by the power inverter and substitute the negative value with this queried value and the delta_energy will be considered as "0" (zero) in the first time running of the script. The delta_energy will only be non-zero after subsequent queries to the API that return values greater than the etotal_inv1_ant value.

3- No file
    If there is no lastenergy.json file, the script will generate an empty file and will behave the same way as when the etotal_inv1_ant value is negative. 

In order to create the file, use following data:
```yaml
{
    "etotal_inv1_ant": 1000.1
    "etotal_inv2_ant": 1000.1
    .
    .
    .
    "etotal_invN_ant": 1000.1
}
```
A sample file is provided, named lastenergy.json-sample. Rename it by removing the trailing string "-sample", and edit it with the proper data.

### Configure the Telegram report 
Open the send_report.py file and insert the chat id and the token from the bot on your Telegram

### Run the code 
To run the main loop, import the request_inverter script

```python
import request_inverter
```

from xrpl.wallet import Wallet
from xrpl.clients import WebsocketClient
from xrpl.models.transactions import Payment, PaymentFlag, Memo
import xrpl
import logging
import json
from check_book_offer import check_price, check_status_transaction
from decimal import *
import asyncio
from send_report import send_report
import time

getcontext().prec = 7
Max_Ledgers_to_Wait = 5
TimeOutSeq = Max_Ledgers_to_Wait * 4

logging.basicConfig(filename="logging.txt", level=logging.INFO, format="%(asctime)s %(message)s")

WS_URL = "wss://rippled.thingsgo.online:6005"

# Do not run the code without the sender data file created
"""{"SENDER_ADDRESS": "", 
    "SENDER_SECRET": "", 
    "FEE": "20", 
    "DESTINATION" : "", 
    "AMOUNT_CURRENCY" : "", 
    "AMOUNT_issuer" : "", 
    "SEND_CURRENCY" : "", 
    "SEND_ISSUER" : ""
    }
"""
with open("send_data.json", "r") as send_data:
    send_data_js = json.loads(send_data.read())
    send_data.close()

client = WebsocketClient(WS_URL)
client.open()

def prepare_transaction(send_max, amount, total):
    memoObj = {
      "name": "Solar Energy Generated",
      "unit": "kWh",
      "delta_value": send_max,
      "total_value": total
    }
    memo_str=json.dumps(memoObj)

    # create a dictionary with the values for the memo transaction
    memo_dict = {
        "memo_format": bytes("application/json","utf-8").hex().upper(),
        "memo_data":  bytes(memo_str,"utf-8").hex().upper()
    }
    # create a Memo transaction object from the dictionary using the from_dict() method
    memo_tx = Memo.from_dict(memo_dict)

    # Define the sending account's wallet
    seq = xrpl.account.get_next_valid_seq_number(send_data_js["SENDER_ADDRESS"], client)
    sender_wallet = Wallet(send_data_js["SENDER_SECRET"], sequence=seq)

    # Create a Payment transaction for the recipient
    payment = Payment(
        account=send_data_js["SENDER_ADDRESS"],
        amount=xrpl.models.amounts.issued_currency_amount.IssuedCurrencyAmount(
            currency=send_data_js["AMOUNT_CURRENCY"],
            issuer=send_data_js["AMOUNT_ISSUER"],
            value=amount
        ),
        send_max=xrpl.models.amounts.issued_currency_amount.IssuedCurrencyAmount(
            currency=send_data_js["SEND_CURRENCY"],
            issuer=send_data_js["SEND_ISSUER"],
            value=send_max
        ),
        destination=send_data_js["DESTINATION"],
        fee=send_data_js["FEE"],
        flags=[PaymentFlag.TF_PARTIAL_PAYMENT],
        last_ledger_sequence=xrpl.ledger.get_latest_validated_ledger_sequence(client) + Max_Ledgers_to_Wait,
        sequence=sender_wallet.sequence,
        memos=[memo_tx]
    )

    # Sign the Payment transaction with the sender's secret key
    pay_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction=payment,
        wallet=sender_wallet,
        client=client,
        check_fee=False
    )
    return pay_prepared

def send_transaction(value, total, WS_URL=WS_URL):
    price = check_price(send_data_js, WS_URL)
    amount = "{:.6f}".format(Decimal(price)*Decimal(value)*Decimal('1.000001'))
    send_max = "{:.6f}".format(Decimal(value))
    print("Amount = " + amount + " | send_max = " + send_max)
    pay_prepared = prepare_transaction(send_max, amount, total)
    #send_report("Sending " + amount + " TGO  with " + send_max + " KWH")
    response = xrpl.transaction.submit_transaction(pay_prepared, client)
    response = response.result
    print(response)

    if(response["engine_result"] == "tesSUCCESS"):
        logging.info("The transaction was applied in a validated ledger. Result: " + response["engine_result"])
        return(response["engine_result"], response["tx_json"]["hash"])

    elif ((response["engine_result"] == "terQUEUED") or (response["engine_result"] == "telINSUF_FEE_P")):
        logging.info("The transaction has been queued for a future ledger. Result: " + response["engine_result"])
        ts = time.time()
        time.sleep(TimeOutSeq)
        tx_hash = response["tx_json"]["hash"]
        transaction_response = check_status_transaction(tx_hash, WS_URL)

        if ('error' in transaction_response):
            logging.info("Transaction not found. Error:" + transaction_response["error"])
            return(None, response["tx_json"]["hash"])
        else:
            if(('status' in transaction_response) and (transaction_response["status"] == "success")):
                if(('result' in transaction_response) and ('meta' in transaction_response["result"]) and ('TransactionResult' in transaction_response["result"]["meta"])):
                    if(transaction_response["result"]["meta"]["TransactionResult"] == "tesSUCCESS"):
                        logging.info("The queued transaction was applied. Result: " + transaction_response["result"]["meta"]["TransactionResult"])
                        send_report("The queued transaction was applied. Result: " + transaction_response["result"]["meta"]["TransactionResult"])
                    else:
                        logging.info("The queued transaction has failed. Result: " + transaction_response["result"]["meta"]["TransactionResult"])
                        send_report("The queued transaction has failed. Result: " + transaction_response["result"]["meta"]["TransactionResult"])
                    return(transaction_response["result"]["meta"]["TransactionResult"], transaction_response["result"]["hash"])
                else:
                    logging.info("No result or result[meta] or result[meta][TransactionResult] found in transaction hash response.")
                    send_report("No result or result[meta] or result[meta][TransactionResult] found in transaction hash response.")
                    return(None, transaction_response)
            else:
                logging.info("No status or status not equal to success found in transaction hash response.")
                send_report("No status or status not equal to success found in transaction hash response.")
                return(None, transaction_response)

    elif ((response["engine_result"] == "terINSUF_FEE_B") or (response["engine_result"] == "tecINSUFF_FEE")):
        logging.info("The account sending the transaction does not have enough XRP to pay the Fee specified in the transaction. Result: " + response["engine_result"])
        send_report("Your account does not have enough XRP to pay the Fee for the transactions")
        return(response["engine_result"], response["tx_json"]["hash"])

    elif (response["engine_result"] == "tecINSUFFICIENT_FUNDS"):
        logging.info("Transaction failed, One of the accounts involved does not hold enough of a necessary asset. Result: " + response["engine_result"])
        send_report("Please check the funds of your account")
        return(response["engine_result"], response["tx_json"]["hash"])

    elif (response["engine_result"] == "tecPATH_PARTIAL"):
        logging.info("Transaction failed, the provided paths did not have enough liquidity to send the full amount. Result: " + response["engine_result"])
        send_report("Please check the funds of your account")
        return(response["engine_result"], response["tx_json"]["hash"])

    elif (response["engine_result"][0:3] == "tec"):
        logging.info("Transaction failed, but it was applied to a ledger to apply the transaction cost. Result: " + response["engine_result"])
        return(response["engine_result"], response["tx_json"]["hash"])

    elif (response["engine_result"][0:3] == "tem"):
        logging.info("Transaction was malformed, and cannot succeed according to the XRP Ledger protocol. Result: " + response["engine_result"])
        return(response["engine_result"], response["tx_json"]["hash"])
        #This should never happens return in a well builded script
        #send_report("Something went wrong in the software, please contact the assistance")

    #elif (response["engine_result"][0:3] == "tel"):
    #   Should be implemeted in the future when added a second things go online server
    #   Retry the transaction on another server

    elif response["engine_result"]:
        logging.info("Error not expected. Result: " + response["engine_result"])
        return(response["engine_result"], response["tx_json"]["hash"])

    else:
        logging.info("No engine_result was found")
        return(None, response["tx_json"]["hash"])

# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 11:31:56 2018

@author: MSeidl
"""


# Import necessary libraries

BlockStart = int(input('enter the first Block to be scanned: '))
BlockEnd = int(input('enter the last Block to be scanned: '))


class ReturnValue(object):
    def __init__(self):
        self.AuctionID = 0
        self.MCP = 0
        self.AmountProduced = 0
        self.AmountConsumed = 0
        self.numberParticipants = 0
        self.minRate = 0
        self.maxRate = 0
        self.MCPTime = 0
        self.BalanceCongestion = 0
        self.BalanceFrequency = 0
        self.BalanceVoltage = 0
        self.TransferedOutside = 0

import web3
import json
import datetime
import pandas as pd
import logging

from web3 import Web3, IPCProvider, HTTPProvider
from web3.middleware import geth_poa_middleware

# Logging, based on: https://docs.python.org/3/howto/logging-cookbook.html
logger = logging.getLogger("MarketLog")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("Logs/" + datetime.datetime.now().isoformat().replace(":","_")[:19] + "_MarketLog.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG) #change this later to Info
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

fr = open('DA_address.txt')
DA_Address = fr.read().split('\n')[0]
fr.close()
fr = open('Register_address.txt')
R_Address = fr.read().split('\n')[0]
fr.close()
fr = open('web3_host.txt')
web3_host = fr.read().split('\n')[0]
fr.close()

fr = open('compiled_sol.json')
compiled_sol = fr.read()
fr.close()
compiled_sol = json.loads(compiled_sol)

# TO BE IMPLEMENTED (bei nächsten Markt Neustart wird GridFee auch mit abgespeichert)
#GF_Address = "0x1d27b6552BD56D88Db230CfEE98a7Db0C9Fa3614"


# Establishing Connection to Local Ganache Blockchain
web3 = Web3(HTTPProvider(web3_host))
web3.middleware_stack.inject(geth_poa_middleware, layer=0)


# Connect to existing Double Auction and GridFee contract
contract_interface = compiled_sol['<stdin>:' + 'DoubleAuction']
DA_Contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
DA_Contract = DA_Contract(DA_Address)

#contract_interface = compiled_sol['<stdin>:' + 'GridFee']
#GF_Contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
#GF_Contract = GF_Contract(GF_Address)

contract_interface = compiled_sol['<stdin>:' + 'Register']
R_Contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
R_Contract = R_Contract(R_Address)

columnNames = ['AuctionID', 'MCP', 'minRate', 'maxRate', 'MCPTime', 'AmountProduced', 'AmountConsumed', 
               'BalanceCongestion', 'BalanceFrequency', 'BalanceVoltage','NumberOfBids','TransferedOutside']

#create csv file only with column headers
df = pd.DataFrame(columns=columnNames)
csv_name = "CSVs/" + datetime.datetime.now().isoformat().replace(":","_")[:19] + "_MarketListener.csv"
df.to_csv(csv_name, sep='\t', encoding='utf-8')
f = open(csv_name, 'a') # Open csv file in append mode

Output = []
Output.append(ReturnValue())

def fillCSV():
    for i in range (len(Output)):
        df = pd.DataFrame(columns=columnNames,index=range(1))
        df['AuctionID'] = Output[i].AuctionID
        df['MCP'] = Output[i].MCP
        df['minRate'] = Output[i].minRate
        df['maxRate'] = Output[i].maxRate
        df['MCPTime'] = Output[i].MCPTime
        df['AmountProduced'] = Output[i].AmountProduced
        df['AmountConsumed'] = Output[i].AmountConsumed
        df['NumberOfBids'] = Output[i].numberParticipants
        df['BalanceCongestion'] = Output[i].BalanceCongestion
        df['BalanceFrequency'] = Output[i].BalanceFrequency
        df['BalanceVoltage'] = Output[i].BalanceVoltage
        #'TransferedOutside'
        
        df.to_csv(f, header = False, encoding='utf-8',index=False)
        logger.info("in CSV AuctionID: " + str(Output[i].AuctionID))
    f.close()
try:
    counter = BlockStart
    counterIDs = 0
    IDdict = {0:0, 1:1}
    while True:
        for i in range(counter,web3.eth.blockNumber+1):
            if i == BlockEnd:
                fillCSV()
                logger.info("DONE")
                exit()
            
            logger.debug('BlockNumber: ' + str(i))
            if web3.eth.getBlock(i)['transactions']:
                logger.info("Transactions exist in Block: " + str(i))
                
                tx_hash = web3.eth.getBlock(i)['transactions'][0]
                tx_hash_hex = tx_hash.hex()
                txn_receipt = web3.eth.getTransactionReceipt(tx_hash)

                log = DA_Contract.events.NewMcp().processReceipt(txn_receipt)
                for j in range(len(log)):
                    x1 = log[j]['transactionHash'].hex()
                    if x1 == tx_hash_hex:
                        AuctionID_new = log[j]['args']['AuctionID']
                        IDdict[AuctionID_new] = counterIDs
                        counterIDs += 1
                        logger.info('new MCP with AuctionID: ' + str(AuctionID_new))
                        
                        Output.append(ReturnValue())
                       
                        Output[IDdict[AuctionID_new]].AuctionID = AuctionID_new
                        Output[IDdict[AuctionID_new]].MCP = log[j]['args']['cbid']
                        Output[IDdict[AuctionID_new]].minRate = log[j]['args']['minRate']
                        Output[IDdict[AuctionID_new]].maxRate = log[j]['args']['maxRate']
                        Output[IDdict[AuctionID_new]].MCPTime = log[j]['args']['NewBlockTime']
                        break

                log = DA_Contract.events.EscrowEvent().processReceipt(txn_receipt)
                for j in range (len(log)):
                    x1 = log[j]['transactionHash'].hex()
                    if x1 == tx_hash_hex:
                        AuctionID_Escrow = log[j]['args']['_AuctionID']
                        logger.info("AuctionID Escrow: " + str(AuctionID_Escrow))
                        
                        if AuctionID_Escrow in IDdict:
                            Output[IDdict[AuctionID_Escrow]].AmountProduced = log[j]['args']['amountProduced']
                            Output[IDdict[AuctionID_Escrow]].AmountConsumed = log[j]['args']['amountConsumed']
                            Output[IDdict[AuctionID_Escrow]].numberParticipants = log[j]['args']['numberParticipants']
                        else:
                            logger.info("Escrow Key not in Array!")
                        break
                
                log = R_Contract.events.TrafoBalances().processReceipt(txn_receipt)
                for j in range (len(log)):
                    x1 = log[j]['transactionHash'].hex()
                    if x1 == tx_hash_hex:
                        AuctionID_bal = log[j]['args']['AuctionID']
                        logger.info("AuctionID Balance: " + str(AuctionID_bal))
                        
                        if AuctionID_bal in IDdict:
                            Output[IDdict[AuctionID_bal]].BalanceCongestion = log[j]['args']['BalanceCongestion']
                            Output[IDdict[AuctionID_bal]].BalanceFrequency = log[j]['args']['BalanceFrequency']
                            Output[IDdict[AuctionID_bal]].BalanceVoltage = log[j]['args']['BalanceVoltage']
                        else:
                            logger.info("Balance Key not in Array!")
                        break
        counter = i+1

except KeyboardInterrupt:
    fillCSV()
    logger.info("Ausführung erfolgreich beendet")
except Exception as e:
    logger.debug("unexpected error")
    logger.error("what happened here?", exc_info=True)
    fillCSV()

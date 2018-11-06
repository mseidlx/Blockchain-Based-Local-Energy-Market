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
        self.BlockNumber = 0
        self.TransactionCount = 0
        self.GasUsed = 0
        self.Difficulty = 0 
        self.GasLimit = 0
        self.Miner = 0 
        self.Size = 0
        self.Timestamp = 0
        self.UncleCount = 0
        
        
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
fh = logging.FileHandler("Logs/" + datetime.datetime.now().isoformat().replace(":","_")[:19] + "_ChainLog.log")
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

columnNames = ['Blocknumber', 'TransactionCount', 'GasUsed', 'GasLimit', 'Difficulty', 'Miner', 'Size', 'TimeStamp', 'UncleCount']

#create csv file only with column headers
df = pd.DataFrame(columns=columnNames)
csv_name = "CSVs/" + datetime.datetime.now().isoformat().replace(":","_")[:19] + "_ChainListener.csv"
df.to_csv(csv_name, sep='\t', encoding='utf-8')
f = open(csv_name, 'a') # Open csv file in append mode

Output = []
Output.append(ReturnValue())

def fillCSV():
    for i in range (len(Output)):
        df = pd.DataFrame(columns=columnNames,index=range(1))
        df['Blocknumber'] = Output[i].BlockNumber
        df['TransactionCount'] = Output[i].TransactionCount
        df['GasUsed'] = Output[i].GasUsed
        df['GasLimit'] = Output[i].GasLimit 
        df['Difficulty'] = Output[i].Difficulty
        df['Miner'] = Output[i].Miner
        df['Size'] = Output[i].Size
        df['TimeStamp'] = Output[i].Timestamp
        df['UncleCount'] = Output[i].UncleCount
        
        df.to_csv(f, header = False, encoding='utf-8',index=False)
        logger.info("in CSV BlockNumber: " + str(Output[i].BlockNumber))
    f.close()
try:
    counter = BlockStart
    counterIDs = 0
    while True:
        for i in range(counter,web3.eth.blockNumber+1):
            if i == BlockEnd:
                fillCSV()
                logger.info("DONE")
                exit()
            
            Output.append(ReturnValue())
            counterIDs += 1
            
            logger.info('BlockNumber: ' + str(i))
            
            block = web3.eth.getBlock(i)
            Output[counterIDs].BlockNumber = i
            Output[counterIDs].TransactionCount = web3.eth.getBlockTransactionCount(i)
            Output[counterIDs].GasUsed = block['gasUsed']
            Output[counterIDs].GasLimit = block['gasLimit']
            Output[counterIDs].Difficulty = block['difficulty']
            Output[counterIDs].Miner = block['miner']
            Output[counterIDs].Size = block['size']
            Output[counterIDs].Timestamp = block['timestamp']
            Output[counterIDs].UncleCount = len(block['uncles'])

        counter = i+1

except KeyboardInterrupt:
    fillCSV()
    logger.info("Ausführung erfolgreich beendet")
except Exception as e:
    logger.debug("unexpected error")
    logger.error("what happened here?", exc_info=True)
    fillCSV()

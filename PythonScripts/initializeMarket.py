# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 15:58:21 2018

@author: MSeidl
"""

blockzeit = 5

# Import necessary libraries
import web3
import time
import json

from solc import compile_source
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

fr = open('web3_host.txt')
web3_host = fr.read().split('\n')[0]
fr.close()

# Establishing Connection to Local Ganache Blockchain
web3 = Web3(HTTPProvider(web3_host))

# Setting the default account to the first account of the Ganache Blockchain and verifying the connection
web3.eth.defaultAccount = web3.eth.accounts[0]

# Checking the coinbase (where the mining rewards are going) 
# Setting the defaultBlock to the last Block (current head of the Blockchain)
coinbase = web3.eth.coinbase
web3.eth.defaultBlock = "latest"

web3.middleware_stack.inject(geth_poa_middleware, layer=0)

# store the accounts in list
accounts = []
for i in range(0,5):
    accounts.append (web3.eth.accounts[i])
    
# compile the Solidity file with all Smart Contracts
contract_source_code = "pragma solidity ^0.4.23; pragma experimental ABIEncoderV2;"
fr = open('FAUCoin.sol')
openTxt = fr.read()
fr.close()
openTxt = openTxt.split('\n',9)[-1]
contract_source_code = contract_source_code + openTxt
fr = open('Register.sol')
openTxt = fr.read()
fr.close()
openTxt = openTxt.split('\n',9)[-1]
contract_source_code = contract_source_code + openTxt
fr = open('GridFee.sol')
openTxt = fr.read()
fr.close()
openTxt = openTxt.split('\n',9)[-1]
contract_source_code = contract_source_code + openTxt
fr = open('DoubleAuction.sol')
openTxt = fr.read()
fr.close()
openTxt = openTxt.split('\n',9)[-1]
contract_source_code = contract_source_code + openTxt
compiled_sol = compile_source(contract_source_code)
#abi = compiled_sol['<stdin>:DoubleAuction']['abi']

# deploy All necessary Smart Contracts
SmartContracts =[None]*4
SmartContractsAddresses =[None]*4
SmartContractsNames = ['Register','FAUCoin','GridFee','DoubleAuction']

for i, SC in enumerate(SmartContractsNames):
    contract_interface = compiled_sol['<stdin>:' + SC]
    SmartContracts[i] = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    tx_hash = SmartContracts[i].deploy(transaction={'from': web3.eth.accounts[0], 'gas': 18000000})
    print(str(SmartContractsNames[i]) + " contract successfully deployed") 
    #print(str(SmartContractsNames[i]) + " ABI: " + str(contract_interface['abi']))
    time.sleep(blockzeit*2)
    
    tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
    SmartContractsAddresses[i] = tx_receipt['contractAddress']
    SmartContracts[i] = SmartContracts[i](tx_receipt['contractAddress'])

# Create Dictionaries for accessing SCs
SCDictAddresses = dict(zip(SmartContractsNames,SmartContractsAddresses,))
SCDictContracts = dict(zip(SmartContractsNames,SmartContracts))

time.sleep(blockzeit+3)

# REGISTER
SCDictContracts['Register'].transact({'from': coinbase}).setFAUCoin(SCDictAddresses['FAUCoin'])

# FAU COIN
SCDictContracts['FAUCoin'].transact({'from': coinbase}).setContractAddress(SCDictAddresses['DoubleAuction'],True)
SCDictContracts['FAUCoin'].transact({'from': coinbase}).setContractAddress(SCDictAddresses['Register'],True)

# GRID FEE
SCDictContracts['GridFee'].transact({'from': coinbase}).setRegister(SCDictAddresses['Register'])
SCDictContracts['GridFee'].transact({'from': coinbase}).setContractAddress(SCDictAddresses['DoubleAuction'],True)

# DAUGHTER AUCTION
SCDictContracts['DoubleAuction'].transact({'from': coinbase}).setContracts(SCDictAddresses['Register'],SCDictAddresses['FAUCoin'],SCDictAddresses['GridFee'])

time.sleep(blockzeit+3)

# Register Trafo with 4 addresses for Grid, Congestion, Frequency and voltage
SCDictContracts['Register'].transact({'from': coinbase}).addTrafo(accounts[1],accounts[2],accounts[3],accounts[4], 9311, 30000)

# Write necessary information for agents
with open("DA_address.txt", "w") as text_file:
    text_file.write(str(SCDictAddresses['DoubleAuction'])) #print(str(SCDictAddresses['DoubleAuction']), file=text_file)
with open("Register_address.txt", "w") as text_file:
    text_file.write(str(SCDictAddresses['Register']))
with open("GridFee_address.txt", "w") as text_file:
    text_file.write(str(SCDictAddresses['GridFee']))
with open("FAUCoin_address.txt", "w") as text_file:
    text_file.write(str(SCDictAddresses['FAUCoin']))    

fw = open('compiled_sol.json', 'w+')
json.dump(compiled_sol, fw)
fw.close()

# Print necessary information for agents
print("DoubleAuction Address: " + str(SCDictAddresses['DoubleAuction']))
print("Register Address: " + str(SCDictAddresses['Register']))
print("GridFee Address: " + str(SCDictAddresses['GridFee']))
print("FAUCoin Address: " + str(SCDictAddresses['FAUCoin']))

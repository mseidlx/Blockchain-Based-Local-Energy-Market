# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 11:53:04 2018

@author: MSeidl
"""

#Constants
blockzeit = 5
_trafo = 9311
_circuit = 1

import time
import json
import socket
import datetime
import pandas as pd
from random import randint
from classAgent import agent

try:    
    columnNames = ['AgentNumber','AgentAddress', 'AgentType', 'BatteryCapacity', 'CurrentBatteryLoad', 'Circuit', 
                   'Trafo', 'BiddingType', 'TimePassed',
                   'Bid_TimeStamp','AuctionID','MCP', 'Bid_Amount','Bid_Label','Bid_Price','TX_Hash_Bid', 
                   'GasBid', 'BlockBid', 'Used_Timestamp', 
                   'Used_Amount', 'Used_Label', 'Voltage', 'Frequency', 'TX_Hash_Usage', 'GasUsage', 'BlockUsage', 
                   'FeeVoltage', 'FeeFrequency', 'FeeCongestion', 'TransferPrice', 'TransferType', 'Payment', 'Balance']
    
    bidding_type = 1
    battery_capacity = randint(50000,100000)
    #agent_name =  str(input('enter the Name of this agent: '))
    agent_name = socket.gethostname()
    agent_type = int(input('enter 1 for Random, 2 for PV, 3 for Household, 4 for Wind: '))
    
    if agent_type == 2:
        type_number = int(input('enter a number to choose the input data: 0-7 for PV: '))
    elif agent_type == 3:
        type_number = int(input('enter a number to choose the input data: 0-16 for Households: '))
    elif agent_type == 4: 
        type_number = int(input('enter a number to choose the input data: 0-2 for Wind: '))
    else:
        type_number = 0
        
    agent_int = int(input('enter 1 for ZI Agent or 2 for Intelligent Bidding Agents: '))
        
    fr = open('DA_address.txt')
    DA_Address = fr.read().split('\n')[0]
    fr.close()
    fr = open('Register_address.txt')
    Register_Address = fr.read().split('\n')[0]
    fr.close()
    fr = open('FAUCoin_address.txt')
    Coin_Address = fr.read().split('\n')[0]
    fr.close()
    fr = open('web3_host.txt')
    web3_host = fr.read().split('\n')[0]
    fr.close()
    
    fr = open('compiled_sol.json')
    compiled_sol = fr.read()
    fr.close()
    compiled_sol = json.loads(compiled_sol)
    
    #create csv file only with column headers
    df = pd.DataFrame(columns=columnNames)
    csv_name = "CSVs/" + datetime.datetime.now().isoformat().replace(":","_")[:19] + "_Agent_" + str(agent_name) + ".csv"
    df.to_csv(csv_name, sep='\t', encoding='utf-8')
    csv_f = open(csv_name, 'a') # Open csv file in append mode 
    
    
    agent_obj = agent(DA_Address,Register_Address, Coin_Address, agent_name, _trafo, _circuit, web3_host, compiled_sol, agent_type, type_number, bidding_type, battery_capacity, agent_int)
    
    counter = 0
    while(True):
        AgentOutput = agent_obj.MarketInteraction()
        counter = counter + 1
        if AgentOutput != None:
            df = pd.DataFrame(columns=columnNames,index=range(1))
            df['AgentNumber'] = AgentOutput.AgentNumber
            df['AgentAddress'] = AgentOutput.AgentAddress
            df['AgentType'] = AgentOutput.AgentType
            df['BatteryCapacity'] = AgentOutput.BatteryCapacity
            df['CurrentBatteryLoad'] = int(AgentOutput.CurrentBatteryLoad)
            df['BiddingType'] = AgentOutput.BiddingType
            df['TimePassed'] = AgentOutput.TimePassed
            df['Circuit'] = AgentOutput.Circuit
            df['Trafo'] = AgentOutput.Trafo
            df['Bid_TimeStamp'] = AgentOutput.BidTimestamp
            df['AuctionID'] = AgentOutput.AuctionID
            df['MCP'] = AgentOutput.MCP
            df['Bid_Amount'] = AgentOutput.Amount
            df['Bid_Label'] = AgentOutput.Label
            df['Bid_Price'] = AgentOutput.Price                
            df['Used_Label'] = AgentOutput.LabelUsed
            df['Used_Amount'] = AgentOutput.AmountUsed
            df['Voltage'] = AgentOutput.Voltage
            df['Used_Timestamp'] = AgentOutput.UsedTimestamp
            #df['FeeVoltage'] = VoltageFee
            #df['FeeFrequency'] = FrequencyFee
            #df['FeeCongestion'] = CongestionFee
            #df['TransferPrice'] = TransferPrice
            #df['TransferType'] = TransferType
            #df['Payment'] = reward
            df['Balance'] = AgentOutput.Balance
            df['GasBid'] = AgentOutput.GasBid
            df['BlockBid'] = AgentOutput.BlockBid
            df['GasUsage'] = AgentOutput.GasUsage
            df['BlockUsage'] = AgentOutput.BlockUsage
            
            if AgentOutput.bid_hash != 0:
                df['TX_Hash_Bid'] = AgentOutput.bid_hash.hex()
                #self.df['Frequency'] = frequencies[AgentOutput.AuctionID]
            else:
                df['TX_Hash_Bid'] = 0
                df['Frequency'] = 0
                
            if AgentOutput.usage_hash != 0:
                df['TX_Hash_Usage'] = AgentOutput.usage_hash.hex()
            else:
                df['TX_Hash_Usage'] = 0
    
            df.to_csv(csv_f, header = False, encoding='utf-8',index=False)
        
        print('### successfull interaction - waiting for next AuctionID ###')
        if agent_type != 1:
            if counter == 670:
                csv_f.close()
                print("Ausführung erfolgreich beendet nach 670 AuctionIDs")
                break
              
        time.sleep(blockzeit) 
        
except KeyboardInterrupt:
    csv_f.close()
    print("Ausführung erfolgreich beendet")

except Exception as e:
    csv_f.close()
    print("unexpected Error in startAgent", exc_info=True)  
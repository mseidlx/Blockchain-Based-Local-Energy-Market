# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 16:02:21 2018

@author: MSeidl
"""
voltageFlag = 1 # 0 equals 23000 from csv, 1 equals Data with peaks from csv, 2 equals randints
blockzeit = 5

import csv
import time
import logging
import requests
import random
import datetime

#from solc import compile_source
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from random import randint
from classReturnValue import ReturnValue

### Für wirklichen Test wieder mit aufnehmen!
random.seed(1)

class agent(object):
    DA_Contract = 0
    my_account = 0
    agentNumber = 0
    f = 0
    
    def __init__(self, DA_Address, Register_Address, Coin_Address, Agent_Number, _Trafo, _Circuit, web3_host, compiled_sol, agenttype, typeCounter, biddingType, batteryCapacity, agent_int):
        # Logging, based on: https://docs.python.org/3/howto/logging-cookbook.html    
        self.logger = logging.getLogger("Agents")
        if (self.logger.hasHandlers()):
            self.logger.handlers.clear()
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler("Logs/" + datetime.datetime.now().isoformat().replace(":","_")[:19] + "_Agent_" + str(Agent_Number) + ".log")
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.agentNumber = Agent_Number
        self.Output = []
        self.Trafo = _Trafo
        self.Circuit = _Circuit
        self.AgentType = agenttype # 1=Random, 2=PV, 3=Haushaltslast, 4=Wind
        self.biddingType = biddingType
        self.lastMCP = 0
        self.BatCapacity = batteryCapacity
        self.CurrentBatLoad = randint(int(batteryCapacity/4), int(batteryCapacity/4 * 3))
        self.timePassed = 0
        self.agentInt = agent_int
        
        # Establishing Connection to Local Ganache Blockchain
        self.web3 = Web3(HTTPProvider(web3_host))
        self.web3.middleware_stack.inject(geth_poa_middleware, layer=0)

        # Connect to existing Double Auction and Register contract
        self.contract_interface = compiled_sol['<stdin>:' + 'DoubleAuction']
        self.DA_Contract = self.web3.eth.contract(abi=self.contract_interface['abi'], bytecode=self.contract_interface['bin'])
        self.DA_Contract = self.DA_Contract(DA_Address)

        self.contract_interface = compiled_sol['<stdin>:' + 'Register']
        self.Register_Contract = self.web3.eth.contract(abi=self.contract_interface['abi'], bytecode=self.contract_interface['bin'])
        self.Register_Contract = self.Register_Contract(Register_Address)
        
        self.contract_interface = compiled_sol['<stdin>:' + 'FAUCoin']
        self.Coin_Contract = self.web3.eth.contract(abi=self.contract_interface['abi'], bytecode=self.contract_interface['bin'])
        self.Coin_Contract = self.Coin_Contract(Coin_Address)

        self.my_account = self.web3.eth.accounts[0]
        self.Register_Contract.functions.addParticipant(self.my_account, self.Trafo, self.Circuit, 1).transact({'from': self.my_account,'gas': 5000000, 'gasPrice': Web3.toWei(5,'gwei')})
        self.logger.info("Agent " + str(self.agentNumber) + " Acc: " + str(self.my_account) + 
                         " Type: " + str(self.AgentType) + " TypeCounter: " + str(typeCounter) + 
                         " batteryCapacity: " + str(batteryCapacity) + " Circuit: " + str(self.Circuit) + " registered")    
        
        if voltageFlag == 0:
            with open('SimulationData/voltage_0.csv', 'r') as f:
                reader = csv.reader(f)
                self.voltageData = list(reader)
        else:
            with open('SimulationData/voltage_1.csv', 'r') as f:
                reader = csv.reader(f)
                self.voltageData = list(reader)
        
        if self.AgentType == 2:
            if typeCounter == 0:
                with open('SimulationData/PV_data_1.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 1:
                with open('SimulationData/PV_data_2.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 2:
                with open('SimulationData/PV_data_3.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 3:
                with open('SimulationData/PV_data_4.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 4:
                with open('SimulationData/PV_data_5.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 5:
                with open('SimulationData/PV_data_6.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 6:
                with open('SimulationData/PV_data_7.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            elif typeCounter == 7:
                with open('SimulationData/PV_data_8.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.PVData = list(reader)
            else:
                with open('SimulationData/PV_data_1.csv', 'r') as f:
                    reader = csv.reader(f)
                    your_list = list(reader)    

                for i in range(len(your_list)):
                    if your_list[i][0] != 0:
                        your_list[i][0] = int(int(your_list[i][0]) * randint(90,110) / 100)
                self.PVData = your_list
        
        if self.AgentType == 3:
            if typeCounter == 0:
                with open('SimulationData/HHPV_data_1.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 1:
                with open('SimulationData/HHPV_data_2.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 2:
                with open('SimulationData/HHPV_data_3.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 3:
                with open('SimulationData/HHPV_data_4.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 4:
                with open('SimulationData/HHPV_data_5.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 5:
                with open('SimulationData/HHPV_data_6.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 6:
                with open('SimulationData/HHPV_data_7.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 7:
                with open('SimulationData/HHPV_data_8.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 8:
                with open('SimulationData/HHPV_data_9.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 9:
                with open('SimulationData/HHPV_data_10.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 10:
                with open('SimulationData/HHPV_data_11.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 11:
                with open('SimulationData/HHPV_data_12.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 12:
                with open('SimulationData/HHPV_data_13.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 13:
                with open('SimulationData/HHPV_data_14.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 14:
                with open('SimulationData/HH_data_15.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 15:
                with open('SimulationData/HH_data_16.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            elif typeCounter == 16:
                with open('SimulationData/HH_data_17.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.HHData = list(reader)
            else:
                with open('SimulationData/HHPV_data_1.csv', 'r') as f:
                    reader = csv.reader(f)
                    your_list = list(reader)    

                for i in range(len(your_list)):
                    if your_list[i][0] != 0:
                        your_list[i][0] = int(int(your_list[i][0]) * randint(90,110) / 100)
                self.PVData = your_list
                    
        if self.AgentType == 4:
            if typeCounter == 0:
                with open('SimulationData/Wind_data_1.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.WindData = list(reader)
            elif typeCounter == 1:
                with open('SimulationData/Wind_data_2.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.WindData = list(reader)
            elif typeCounter == 2:
                with open('SimulationData/Wind_data_3.csv', 'r') as f:
                    reader = csv.reader(f)
                    self.WindData = list(reader)
            else:
                with open('SimulationData/Wind_data_1.csv', 'r') as f:
                    reader = csv.reader(f)
                    your_list = list(reader)    

                for i in range(len(your_list)):
                    if your_list[i][0] != 0:
                        your_list[i][0] = int(int(your_list[i][0]) * randint(90,110) / 100)
                self.PVData = your_list
        
    def sendBid(self):
        
        data = self.Output[self.bidCount-1]
        estimatedGas = 0
        amount = data.Amount
        price = data.Price
        label = data.Label
        
        self.logger.debug("Agent " + str(self.agentNumber) + " before Bid amount: " + str(amount) + 
                          " price: " + str(price) + " label: "+ str(label))

        while estimatedGas == 0:
            try:
                estimatedGas = self.DA_Contract.functions.preBid(amount ,price ,label ).estimateGas({'from': self.my_account})
                data.bid_hash = self.DA_Contract.functions.preBid(amount, price, label).transact({'from': self.my_account,'gas': 18000000, 'gasPrice': Web3.toWei(5,'gwei')})
                data.BidTimestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data.Circuit = self.Circuit
                data.Trafo = self.Trafo
                data.Balance = self.Coin_Contract.call().getCoinBalance(self.my_account)
                self.logger.info("Balance: " + str(data.Balance))
                if self.timePassed != 0:
                    self.timePassed = datetime.datetime.now() - self.timePassed
                    data.TimePassed = self.timePassed
                
                #if estimatedGas > 1500000:
                #    self.logger.info("Market just cleared!")
                #    time.sleep(blockzeit)
                    
                self.logger.debug("SEND BID successful! Agent " + str(self.agentNumber) + ": estimated Gas: " + str(estimatedGas) + 
                                  " amount: " + str(amount) + " price: " + str(price) + " label: "+ str(label) +  " time: " + str(self.timePassed) + " hash: " + str(data.bid_hash))
                self.timePassed = datetime.datetime.now()
                
            except ValueError:
                self.logger.debug("Agent " + str(self.agentNumber) + ": waiting with Bid for new AuctionID")
                estimatedGas = 0
                time.sleep(randint(1,3))
            except requests.exceptions.ReadTimeout:
                self.logger.info("Agent " + str(self.agentNumber) + ": Bidding ReadTimeout")
                estimatedGas = 0
                time.sleep(randint(1,3))
            except Exception as e:
                self.logger.info("Agent " + str(self.agentNumber) + ": unexpected error in bidding Loop")
                self.logger.error("Agent " + str(self.agentNumber) + ": unexpected error in bidding Loop", exc_info=True)
                estimatedGas = 0
                time.sleep(2)

    def checkBidReturn(self):
        
        try:
            data = self.Output[self.bidCount-2]
            bid_hash = data.bid_hash

            if bid_hash != 0:
                bid_hash_hex = bid_hash.hex()
                ReceiptReceived = False
                while ReceiptReceived == False:
                    txn_receipt = self.web3.eth.getTransactionReceipt(bid_hash)
                
                    if txn_receipt == None:
                        self.logger.debug("no transaction Receipt yet -> wait 2s")
                        time.sleep(2)
                    else:
                        ReceiptReceived = True
        
                log = self.DA_Contract.events.NewBid().processReceipt(txn_receipt)
                
                for j in range (len(log)):
                    x1 = log[j]['transactionHash'].hex()
                    if x1 == bid_hash_hex:
                        data.AuctionID = log[j]['args']['CurrentAuctionID']
                        data.MCP = log[j]['args']['LastMCP']
                        addr = log[j]['args']['addr']
                        break
                    
                self.lastMCP = data.MCP
                self.logger.debug("CHECK BID RETURN successful! Agent " + str(data.AgentNumber) + ": AuctionID: " + str(data.AuctionID) + " MCP: " + str(data.MCP) + " label: " + str(data.Label) + " amount: " + str(data.Amount) + " price: " + str(data.Price))         
            else:
                self.logger.info("NO checkBidReturn (no bidHash) for  Agent " + str(data.AgentNumber) + " in AuctionID: " +  str(data.AuctionID))
        except Exception as e:
            self.logger.info("Agent " + str(self.agentNumber) + ": unexpected error in checkBidReturn")
            self.logger.error("Agent " + str(self.agentNumber) + ": unexpected error in checkBidReturn", exc_info=True)
            
                
    def sendUsage(self):
        
        data = self.Output[self.bidCount-3]
        bid_hash = data.bid_hash
        
        if bid_hash != 0:
            estimatedGas = 0
            
            if data.AgentType == 3: #if it is a household agent with a battery
                if self.BatCapacity > 0:
                    if data.Label < 10: #producer
                        if data.Price > data.MCP: # was not successful within cell, can store more in battery if possible
                            if ((self.CurrentBatLoad + data.AmountUsed) < self.BatCapacity):
                                self.CurrentBatLoad = self.CurrentBatLoad + data.AmountUsed 
                                data.AmountUsed = 1
                    else: # consumer
                        if data.Price < data.MCP: # was not successful within cell, can use battery if possible
                            if self.CurrentBatLoad > data.AmountUsed:
                                self.CurrentBatLoad = self.CurrentBatLoad - data.AmountUsed 
                                data.AmountUsed = 1
                                
            data.CurrentBatteryLoad = self.CurrentBatLoad                                       
            amount = data.AmountUsed
            label = data.LabelUsed
            
            # Here the voltage input is choosable
            if voltageFlag < 2:
                if self.AgentType == 1:
                    voltage = randint(22800,23200)
                else:
                    voltage = int(self.voltageData[self.bidCount][0])
                #voltage = randint(int(self.voltageData[self.bidCount][0]) - 10, int(self.voltageData[self.bidCount][0] + 10))
            else:
                voltage = randint(22800,23200)
                #voltage = data.Voltage
            
            self.Output[self.bidCount-3].Voltage = voltage

            _AuctionID = data.AuctionID
            
            VECounter = 0
            self.logger.debug("Agent " + str(self.agentNumber) + ": Before Usage Amount: "  + str(amount) + 
                                      " label: " + str(label) + " voltage: "+ str(voltage) + 
                                      " AuctionID " + str(_AuctionID))
            while estimatedGas == 0:
                try:
                    estimatedGas = self.DA_Contract.functions.actualUsage(voltage, amount, label, _AuctionID).estimateGas({'from': self.my_account})
                    data.usage_hash = self.DA_Contract.functions.actualUsage(voltage, amount, label, _AuctionID).transact({'from': self.my_account,'gas': 18000000, 'gasPrice': Web3.toWei(5,'gwei')})
                    data.UsedTimestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.logger.debug("SEND USAGE succesful! Agent " + str(self.agentNumber) + ": estimated Gas for Usage: " + str(estimatedGas) + 
                                      " AuctionID: " + str(_AuctionID))
                except ValueError:
                    self.logger.debug("Agent " + str(self.agentNumber) + ": Usage ValueError")
                    self.logger.debug("Agent " + str(self.agentNumber) + " Amount: "  +str(amount) + 
                                      " label: " + str(label) + " voltage: "+ str(voltage) + 
                                      " AuctionID " + str(_AuctionID))

                    if VECounter > 7:
                        self.logger.info("Agent " + str(self.agentNumber) + " AuctionID " + str(_AuctionID) +": Usage too many ValueError - skipped")
                        break
                    
                    time.sleep(randint(1,3))
                    VECounter = VECounter+1
                    estimatedGas = 0
                except requests.exceptions.ReadTimeout:
                    self.logger.error("Agent " + str(self.agentNumber) + ": Usage ReadTimeout", exc_info=True)
                    self.logger.info("Agent " + str(self.agentNumber) + ": Usage ReadTimeout")
                    estimatedGas = 0
                    time.sleep(randint(1,3))
                except Exception as e:
                    self.logger.info("Agent " + str(self.agentNumber) + ": unexpected error in Usage Loop")
                    self.logger.error("Agent " + str(self.agentNumber) + ": unexpected error in Usage Loop?", exc_info=True)
                    estimatedGas = 0
                    time.sleep(2)
        else:
            self.logger.info("NO sendUsage for  Agent " + str(data.AgentNumber) + " in AuctionID: " +  str(data.AuctionID))
            
    def price_bid(self, level):
        
        if self.bidCount < 5:
            val = val = randint(120,140)
        elif level == 0: #random bid
            val = randint(80,260)
        elif self.lastMCP > 280:
            val = randint(270,279)
        elif self.lastMCP < 70:
            val = randint(71,80)
        
        #Producer
        elif level == 1: # standard producer bid
            val = self.lastMCP - randint(2,6)
        elif level == 2: # Voltage High -> have to offer cheaper
            val = self.lastMCP - randint(6,10)
        elif level == 3: # Voltage Low -> can offer more expensive
            val = self.lastMCP + randint(0,4)
        
        #Consumer
        elif level == 4: # standard consumer bid
            val = self.lastMCP + randint(0,4)
        elif level == 5: # Voltage High -> can buy cheaper
            val = self.lastMCP - randint(0,4)
        elif level == 6: # Voltage Low -> has to pay more
            val = self.lastMCP + randint(4,8)
            
        else:
            val = self.lastMCP

        return val
    
    def random_Values(self):
        data =  self.Output[self.bidCount-1]
        try:                        
            data.Amount = randint(100,1500)
            data.Label = randint(1,19)
            
            if data.Label > 9:
                bidder = randint(4,6)
            else:
                bidder = randint(1,3)
            
            if self.agentInt == 1:
                data.Price = self.price_bid(0)
            else:
                data.Price = self.price_bid(bidder)
                
            data.AmountUsed = int(data.Amount * randint(90,110)/100)
            data.LabelUsed = data.Label
            data.Voltage = randint(22850,23150)
            data.BiddingType = bidder
            
        except Exception as e:
            self.logger.info("Agent " + str(self.agentNumber) + ": Random_Values unexpected error")
            self.logger.error("Agent " + str(self.agentNumber) + ": what happened?", exc_info=True)
    
    def PV_Values(self):
        data = self.Output[self.bidCount-1]
        try:                        
            data.Label = 2
            data.LabelUsed = 2
            data.Voltage = randint(23100,23500)
            data.Amount = int(int(self.PVData[self.bidCount][0])*randint(90,110)/100)+1 #kleine Abweichung
            data.AmountUsed = int(self.PVData[self.bidCount][0])+1
            
            if self.agentInt == 1:
                data.Price = self.price_bid(0)
            else:
                data.Price = self.price_bid(self.biddingType)
                
            data.BiddingType = self.biddingType
            
        except Exception as e:
            self.logger.info("Agent " + str(self.agentNumber) + ": PV_Values unexpected error")
            self.logger.error("Agent " + str(self.agentNumber) + ": what happened?", exc_info=True)
    
    def Wind_Values(self):
        data = self.Output[self.bidCount-1]
        if voltageFlag < 2:
            volDiff = int(self.voltageData[self.bidCount][0]) - 23000
        else:
            volDiff = 10
        
        try:                        
            data.Label = 4
            data.LabelUsed = 4
            data.Voltage = randint(23100,24050)
            data.Amount = int(int(self.WindData[self.bidCount][0])*randint(90,110)/100)+1 #kleine Abweichung
            data.AmountUsed = int(self.WindData[self.bidCount][0])+1
            
            if volDiff > 300:
                data.BiddingType = 2
            elif volDiff < -500:
                data.BiddingType = 3
            else:
                data.BiddingType = 1
                
            if self.agentInt == 1:
                data.Price = self.price_bid(0)
            else:
                data.Price = self.price_bid(self.biddingType)
            
        except Exception as e:
            self.logger.debug("Agent " + str(self.agentNumber) + ": Wind_Values unexpected error")
            self.logger.error("Agent " + str(self.agentNumber) + ": what happened?", exc_info=True)
    
    def Household_Values(self): 
        data = self.Output[self.bidCount-1]
        if voltageFlag < 2:
            volDiff = int(self.voltageData[self.bidCount][0]) - 23000
        else:
            volDiff = 10
        
        try:    
            BatteryUsage = self.CurrentBatLoad/self.BatCapacity
            HH_Usage = int(self.HHData[self.bidCount][0])
            
            if HH_Usage < 0: # check if HH has a demand or supply
                HH_Usage = HH_Usage * (-1)
                HH_Supply = False
            else:
                HH_Supply = True
            
            # 0-20%: Battery Load very low, agent would buy HH energy from market and also the same amount again for battery
            if BatteryUsage < 0.2:
                if HH_Supply == False:
                    if volDiff > 300:
                        HH_price_bid = 5
                        HH_Label = 11
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.2)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + int(self.BatCapacity*0.2)  
                    else:
                        HH_price_bid = 4
                        HH_Label = 11
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.1)
                        HH_Voltage = randint(22000,22500) 
                        self.CurrentBatLoad = self.CurrentBatLoad + int(self.BatCapacity*0.1)
                else:
                    if volDiff > 300: # Agent kauft mehr, da bezuschusst
                        HH_price_bid = 2
                        HH_Label = 2
                        HH_Amount_Market = int(self.BatCapacity*0.05)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + HH_Usage + int(self.BatCapacity*0.05)
                    else:
                        HH_price_bid = 1
                        HH_Label = 2
                        HH_Amount_Market = 0
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + HH_Usage
                
            # 20-50%: Battery Load low, agent only buys at market, if MCP lower than 130, else battery    
            elif BatteryUsage < 0.5:
                if HH_Supply == False:
                    if volDiff > 300: # Agent kauft mehr, da bezuschusst
                        HH_price_bid = 5
                        HH_Label = 11
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.1)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + int(self.BatCapacity*0.1)
                    elif volDiff < -500:
                        HH_price_bid = 3
                        HH_Label = 3
                        HH_Amount_Market = HH_Usage
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - HH_Usage * 2
                    elif self.lastMCP < 140: #Kauf Load + 5% Kapazität  
                        HH_price_bid = 4
                        HH_Label = 11
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.05)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + int(self.BatCapacity*0.05)
                    else: # Kaufe Hälfte der Last am Markt, andere Hälfte Batterie
                        HH_price_bid = 4
                        HH_Label = 11
                        HH_Amount_Market = HH_Usage/2
                        HH_Voltage = randint(22500,23000) 
                        self.CurrentBatLoad = self.CurrentBatLoad - HH_Usage/2
                else:
                    if volDiff > 300: # Agent verkauft weniger, da bestraft
                        HH_price_bid = 2
                        HH_Label = 2
                        HH_Amount_Market = 0
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + HH_Usage
                    elif volDiff < -500: # Agent verkauft mehr, da bezuschusst
                        HH_price_bid = 3
                        HH_Label = 2
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.05)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - int(self.BatCapacity*0.05)
                    elif self.lastMCP > 140: #Verkaufen lohnt sich 
                        HH_price_bid = 1
                        HH_Label = 2
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.05)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - int(self.BatCapacity*0.05)
                    else: # Verkaufen lohnt sich weniger
                        HH_price_bid = 1
                        HH_Label = 2
                        HH_Amount_Market = 0
                        HH_Voltage = randint(22500,23000) 
                        self.CurrentBatLoad = self.CurrentBatLoad + HH_Usage
            
            # 50-80%: Batter Load high, agent only buys at market, if MCP lower than 110
            elif BatteryUsage < 0.8:
                if HH_Supply == False:
                    if volDiff > 300: # Agent kauft mehr, da bezuschusst
                        HH_Label = 11
                        HH_price_bid = 5
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.1)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + int(self.BatCapacity*0.1)      
                    elif volDiff < -500:
                        HH_price_bid = 3
                        HH_Label = 3
                        HH_Amount_Market = int(self.BatCapacity*0.1) 
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - HH_Usage - int(self.BatCapacity*0.1) 
                    elif self.lastMCP < 120: #Kauf Load + 5% Kapazität 
                        HH_Label = 11
                        HH_price_bid = 4
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.05)
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + int(self.BatCapacity*0.05)
                    else: # Nutze nur die Batterie
                        HH_Label = 11
                        HH_price_bid = 4
                        HH_Amount_Market = 0
                        HH_Voltage = randint(22900,23100) 
                        self.CurrentBatLoad = self.CurrentBatLoad - HH_Usage
                else:
                    if volDiff > 300: # Agent verkauft weniger, da Strafe
                        HH_Label = 2
                        HH_price_bid = 2
                        HH_Amount_Market = 0
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad + HH_Usage      
                    elif volDiff < -500: # agent verkauft mehr, da bezuschusst
                        HH_price_bid = 3
                        HH_Label = 2
                        HH_Amount_Market = int(self.BatCapacity*0.1) + HH_Usage
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - int(self.BatCapacity*0.1) 
                    elif self.lastMCP > 120: #Verkaufen lohnt sich 
                        HH_Label = 2
                        HH_price_bid = 1
                        HH_Amount_Market = HH_Usage 
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad
                    else: 
                        HH_Label = 2
                        HH_price_bid = 1
                        HH_Amount_Market = HH_Usage/2
                        HH_Voltage = randint(22900,23100) 
                        self.CurrentBatLoad = self.CurrentBatLoad + HH_Usage/2
            
            # 80-100%: Battery Load very high, agent would take HH energy out of battery and also sell the same amount from bat to market
            else:
                if HH_Supply == False:
                    if volDiff < -500:
                        HH_price_bid = 3
                        HH_Label = 3
                        HH_Amount_Market = int(self.BatCapacity*0.2) 
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - HH_Usage - int(self.BatCapacity*0.2) 
                    else:
                        HH_price_bid = 1
                        HH_Label = 3
                        HH_Amount_Market = int(self.BatCapacity*0.1)
                        self.CurrentBatLoad = self.CurrentBatLoad - HH_Usage -  int(self.BatCapacity*0.1)
                else:
                    if volDiff < -500:
                        HH_price_bid = 3
                        HH_Label = 2
                        HH_Amount_Market = HH_Usage + int(self.BatCapacity*0.15) 
                        HH_Voltage = randint(22100,22700) 
                        self.CurrentBatLoad = self.CurrentBatLoad - int(self.BatCapacity*0.15) 
                    else:
                        HH_price_bid = 1
                        HH_Label = 2
                        HH_Amount_Market = HH_Usage
                        self.CurrentBatLoad = self.CurrentBatLoad
                        
            data.BiddingType = HH_price_bid
            data.CurrentBatteryLoad = self.CurrentBatLoad 
            data.Label = HH_Label
            data.LabelUsed = HH_Label
            data.Voltage = randint(22500,22900)
            data.Amount = int(HH_Amount_Market * randint(90,100)/100) + 1
            data.AmountUsed = int(HH_Amount_Market) + 1 
            
            if self.agentInt == 1:
                data.Price = self.price_bid(0)
            else:
                data.Price = self.price_bid(HH_price_bid)
            
        except Exception as e:
            self.logger.info("Agent " + str(self.agentNumber) + ": Household_Values unexpected error")
            self.logger.error("Agent " + str(self.agentNumber) + ": what happened?", exc_info=True)
    
    
    def setFrequency(self, _AuctionID, frequ):
        self.DA_Contract.functions.setFrequency(_AuctionID, frequ).transact({'from': self.my_account,'gas': 5000000 ,'gasPrice': Web3.toWei(5,'gwei')})
    
    def getLastBidHash(self):
        return self.Output[self.bidCount-1].bid_hash
    
    def getAddress(self):
        return self.my_account
    
    
    # Main Function which is called from outside
    def MarketInteraction(self):
        try:
            #add new object to List
            self.Output.append(ReturnValue())
            
            #count nunber of bids/AuctionIDs whatever
            self.bidCount = len(self.Output)
            self.Output[self.bidCount-1].AgentNumber = self.agentNumber
            self.Output[self.bidCount-1].AgentAddress = self.my_account
            self.Output[self.bidCount-1].AgentType = self.AgentType
            self.Output[self.bidCount-1].BatteryCapacity = self.BatCapacity
            self.Output[self.bidCount-1].Intelligence = self.agentInt
            
            if self.bidCount > 1:
                self.checkBidReturn()
            
            # Select Bidding Values based on bidding type and store them
            if self.AgentType == 1:
                self.random_Values()
            elif self.AgentType == 2:
                self.PV_Values()
            elif self.AgentType == 3:
                self.Household_Values()
            elif self.AgentType == 4:
                self.Wind_Values()
            else:
                self.logger.info("No valid Agenttype!")
                exit()
            
            # send new bid to the blockchain
            self.sendBid()
            
            # Check to see how many bids already exist in order to know which functions are necessarry
            if self.bidCount > 2:
                self.sendUsage()
            
            if self.bidCount > 3:
                data = self.Output[self.bidCount - 4]
                bid_hash = data.bid_hash
                usage_hash = data.usage_hash
                
                if bid_hash != 0:
                    txn_receipt = self.web3.eth.getTransactionReceipt(data.bid_hash)
                    data.GasBid = txn_receipt['gasUsed']
                    data.BlockBid = txn_receipt['blockNumber']
                else:
                    self.logger.debug("NO BID Gas/BlockNumber for  Agent " + str(data.AgentNumber) + 
                                     " in AuctionID: " +  str(data.AuctionID))
                if usage_hash != 0: 
                    txn_receipt = self.web3.eth.getTransactionReceipt(data.usage_hash)
                    data.GasUsage = txn_receipt['gasUsed']
                    data.BlockUsage = txn_receipt['blockNumber']
                else:
                    self.logger.info("NO USAGE Gas/BlockNumber for  Agent " + str(data.AgentNumber) + 
                                     " in AuctionID: " +  str(data.AuctionID))
                
                self.logger.debug("DONE Agent " + str(data.AgentNumber) + " AuctionID: " + str(data.AuctionID) + 
                                 " MCP: " + str(data.MCP) + " Label: " + str(data.Label) + 
                                 " Amount: " + str(data.Amount) + " Price: " + str(data.Price) + " Address: " + str(self.my_account))
                
                self.logger.info("DONE Agent " + str(data.AgentNumber) + " AuctionID: " + str(data.AuctionID) + " BlockBid: " + str(data.BlockBid) + " MCP: " + str(data.MCP))
                return data
            
            else:
                self.logger.info("not enough bids(" + str(self.bidCount) +") yet for agent " + str(self.agentNumber))
                return None
            
    
                
        except Exception as e:
            self.logger.info("unexpected Error in MarketInteraction")
            self.logger.error("unexpected Error in MarketInteraction", exc_info=True)
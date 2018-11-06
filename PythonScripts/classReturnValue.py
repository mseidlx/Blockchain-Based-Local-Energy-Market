# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 16:00:49 2018

@author: MSeidl
"""

class ReturnValue(object):
    def __init__(self):
        self.AgentNumber = 0
        self.AgentAddress = 0
        self.AgentType = 0
        self.BatteryCapacity = 0
        self.CurrentBatteryLoad = 0
        self.Circuit = 0
        self.Trafo = 0
        self.Intelligence = 0
        self.BiddingType = 0
        self.BidTimestamp = 0
        self.UsedTimestamp = 0
        self.AuctionID = 0
        self.MCP = 0
        self.Amount = 0
        self.Label = 0
        self.Price = 0
        self.TimePassed = 0
        self.bid_hash = 0
        self.usage_hash = 0
        self.AmountUsed = 0
        self.LabelUsed = 0
        self.Voltage = 0
        self.Frequency = 0
        self.FeeVoltage = 0
        self.FeeFrequency = 0
        self.FeeCongestion = 0
        self.GasBid = 0
        self.GasUsage = 0
        self.BlockBid = 0
        self.BlockUsage = 0
        self.Balance = 0
    
    def printAll(self):
        print("AgentNumer: " + str(self.AgentNumber))
        print("AgentAddress: " + str(self.AgentAddress))
        print("AgentType: " + str(self.AgentType))
        print("BatteryCapacity: " + str(self.BatteryCapacity))
        print("BatteryLoad: " + str(self.CurrentBatteryLoad))
        print("Circtui: " + str(self.Circuit))
        print("Trafo:" + str(self.Trafo))
        print("BiddingType: " + str(self.BiddingType))
        print("BidTimestamp: " + str(self.BidTimestamp))
        print("UsedTimestamp: " + str(self.UsedTimestamp))
        print("AuctionID: " + str(self.AuctionID))
        print("MCP: " + str(self.MCP))
        print("AmountBid: " + str(self.Amount))
        print("LabelBid: " +str(self.Label))
        print("Price: " + str(self.Price))
        print("TimePassed: " + str(self.TimePassed))
        print("bidHash: " + str(self.bid_hash))
        print("UsageHash: " + str(self.usage_hash))
        print("AmountUsed: " + str(self.AmountUsed))
        print("LabelUsed: " + str(self.LabelUsed))
        print("Voltage: " + str(self.Voltage))
        print("Frequncy: " + str(self.Frequency))
        print("FeeVoltage: " + str(self.FeeVoltage))
        print("FeeFrequency: " + str(self.FeeFrequency))
        print("FeeCongestion: " + str(self.FeeCongestion))
        print("GasBid: " + str(self.GasBid))
        print("GasUsage: " + str(self.GasUsage))
        print("BlockBid: " + str(self.BlockBid))
        print("BlockUsage: " + str(self.BlockUsage))
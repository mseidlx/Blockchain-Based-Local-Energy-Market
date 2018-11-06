//@author: Matthias Seidl
pragma solidity ^0.4.23;
//pragma experimental ABIEncoderV2;

import "browser/Register.sol";
import "browser/FAUCoin.sol";
import "browser/GridFee.sol";


contract DoubleAuction{
    //Variables
    address public owner;
    
    Register register;
    FAUCoin coin;
    GridFee fee;

    uint AuctionID;
    uint32 trafo;
    uint16 GridPriceBuy;
    uint16 GridPriceSell;
    uint16 maxRate = 0;  
    uint16 minRate = 65000;
	uint16 AuctionTime = 30;
    
    bool constant ModCongestionFee = true;
    bool constant ModAutarkFrequencyFee = false; //if Autark and Semi are true Autark will be used!
    bool constant ModSemiAutarkFrequencyFee = false;
    bool constant ModAutarkVoltageFee = true; //if Autark and Semi are true Autark will be used!
    bool constant ModSemiAutarkVoltageFee = false;
    
    
    mapping (uint256 => Details[]) participantsBids; //hierraus ein Array machen?
    mapping (uint256 => Details[]) participantsUsage; //hierraus ein Array machen?
    mapping (uint256 => mapping (address => bool)) BidderBool;
    mapping (uint256 => mapping (address => bool)) UsageBool;
    mapping (uint256 => uint256) Frequencies;
    mapping (uint256 => uint64) MCPs;
    mapping (uint256 => uint256) Timer;
    uint32[] SRate = new uint32[](300); // somit werden nur Preise zwischen 0 und 30ct erlaubt
    uint32[] DRate = new uint32[](300);
    
    //Events 
    event NewBid(address indexed addr, uint64 rate, uint32 amount, uint8 label, uint256 CurrentAuctionID, uint64 LastMCP);
    event NewMcp(uint64 cbid, uint16 minRate, uint16 maxRate, uint256 NewBlockTime, uint256 AuctionID);
    event NewUsage(uint64 _price, uint32 _amount, uint8 _label, uint32 voltage, uint256 _AuctionID, address xaddress);
    event EscrowEvent (uint8 flag, uint32 amountProduced, uint32 amountConsumed, uint256 numberParticipants, uint256 _AuctionID);
    event Transfer(address xaddress, uint32 _amount, uint64 _TransferPrice, int reward, int FrequencyFee, int VoltageFee, int64 CongestionFee, uint8 TransferType, int Balance); //type 1 = Inner, 2 = Outer
    event TimerEvent(string output, uint256 LastBlockTime, uint256 CurrentBlockTime);
    //event TrafoBalances(int BalanceGrid, int BalanceCongestion, int BalanceFrequency, int BalanceVoltage);
    
    //Strcuts
    struct Details {
        uint64 price; // cents/KW
        uint32 amount; // Kw
        uint8 label;
        address xaddress;
        uint32 amount2; // helpful in Escrow Function bc it stores the bidding Amount 
    }
    
    //Constructor
    constructor() public{
        owner = msg.sender;
        trafo=9311;
        AuctionID = 1;
        GridPriceBuy = 80;
        GridPriceSell = 250;
        Timer[0] = block.timestamp;
    }
    
    //Modifiers
    modifier onlyOwner(){
		require(msg.sender == owner);
		_;
	}
    
    modifier onlyValidProsumers(){ //checks if Label is in the prosumer spectrum and correct Trafo and sufficient funds
		require(register.getLabel(msg.sender) < 20); 
		require(trafo==(register.getTrafoID(msg.sender)));
		require(coin.getCoinBalance(msg.sender) > 100000);
	    _;
	}
	
    modifier onlyValidBidders(){
        require(BidderBool[AuctionID-2][msg.sender] == true); 
	    _;
	}
	
	modifier onlyOneBidPerPeriod(){
	    require(BidderBool[AuctionID][msg.sender] == false);
	    _;
	}
	
	modifier onlyOneUsagePerBlock(){
	    require(UsageBool[AuctionID-2][msg.sender] == false);
	    _;
	}
    
    //special Functions
    function checkLabel(uint8 _label) private pure returns (uint8) {
        if (((_label) >= uint8(0)) && (_label < uint8(10))) {
            return 0; // if Label is between 0 and 9 return 0 -> producer
        }else if ((_label >= uint8(10))&&(_label < uint8(20))) {
            return 1; // if Label is between 10 and 19 return 1 -> consumer
        }else {
            return 2; // if Label is 20 or bigger return 2 -> DNO
        }
    }
    
    function preBid(uint32 _amount, uint16 _price, uint8 _label) onlyValidProsumers public{
        if (block.timestamp >= Timer[AuctionID] + AuctionTime){
            emit TimerEvent("Bidding time reached", Timer[AuctionID], block.timestamp);
            MarketClear();
            escrow(AuctionID-3);
        }else{
            emit TimerEvent("Bidding time isn't reached yet", Timer[AuctionID], block.timestamp);
        }
        bid(_amount, _price, _label);
    }
    
    function bid(uint32 _amount, uint16 _price, uint8 _label) onlyOneBidPerPeriod public{ //change to private
        // Mapping  bidding
        
        if (_amount>uint16(0)) {
            participantsBids[AuctionID].push(Details (_price, _amount, _label, msg.sender,0));
            BidderBool[AuctionID][msg.sender] = true;
            if (_price > maxRate) {
                maxRate = _price;
            }
            if (_price < minRate) {
                minRate = _price;
            }
            emit NewBid(msg.sender,_price, _amount, _label, AuctionID, MCPs[AuctionID-1]);
            
            if(checkLabel(_label) == 0){
                SRate[_price] += _amount;
            }else if (checkLabel(_label) == 1){
                DRate[_price] += _amount;
            }
            return;
        }
    }

    function MarketClear() public returns (uint64){ // needs to be changed to private as soon as implemented + modifier added for time (15s)
        // Adding up the Amounts for each price
        uint64 _max = maxRate;
        uint64 y;
        
        //add up the Amounts for each price
        for (y=minRate;y<=maxRate;y++) {
            SRate[y] += SRate[y-1];
            DRate[_max-1] += DRate[_max];
            _max--;
        }
        //Break-Even Finder
        for (y = minRate; y <= maxRate; y++) {
            if (SRate[y] >= DRate[y]) {
                if (DRate[y] > SRate[y-1]) {
                    emit NewMcp(y, minRate, maxRate, block.timestamp, AuctionID);
                    MCPs[AuctionID] = y;
                    reset();
                    return (y);
                } else {
                    emit NewMcp(y-1, minRate, maxRate, block.timestamp, AuctionID);
                    y--;
                    MCPs[AuctionID] = y;
                    reset();
                    return (y);
                }
            }
        }
		//MCPs[AuctionID] = GridPriceSell;
		if (AuctionID > 1){
		    MCPs[AuctionID] = MCPs[AuctionID-1] + 10;
		}else{
		    MCPs[AuctionID] = 130;
		}
		emit NewMcp(MCPs[AuctionID], 999, maxRate, block.timestamp, AuctionID);
		reset();
        return MCPs[AuctionID]; //will only be reached if no Producer Bid exists
    }

    function reset() private{
        for (uint64 w = minRate; w <= maxRate; w++) {
            SRate[w]=0;
            DRate[w]=0;
        }
        
        AuctionID = AuctionID + 1;
        Timer[AuctionID] = block.timestamp;
        maxRate=0;
        minRate=65000;
    }
    
    function actualUsage(uint32 _voltage, uint32 _amount, uint8 _label, uint256 _AuctionID) onlyValidBidders onlyOneUsagePerBlock public {
        // Mapping Producers actualUsage
        uint64 _price;
        uint32 _amount2;
        if (_amount>=uint32(0)) {
            // get bidding price
            for (uint8 i=0; i<= participantsBids[_AuctionID].length; i++){
                if (participantsBids[_AuctionID][i].xaddress == msg.sender){
                    _price = participantsBids[_AuctionID][i].price;
                    _amount2 = participantsBids[_AuctionID][i].amount;
                    break;
                }
            }
            participantsUsage[_AuctionID].push(Details (_price, _amount, _label,msg.sender, _amount2));
            UsageBool[_AuctionID][msg.sender] = true;
            fee.RegisterVoltage(register.getCircuit(msg.sender),_voltage, _AuctionID);
            emit NewUsage(_price, _amount, _label, _voltage, _AuctionID, msg.sender);
        }
        
    }
    
    function innerTransferMoney(uint256 _AuctionID, uint32 _amount, uint8 _label, address _address) private{
        int reward;
        int FrequencyFee;
        int VoltageFee;
        
        if (ModAutarkFrequencyFee == true){
            FrequencyFee = fee.AutarkFrequencyFee(_amount, checkLabel(_label), Frequencies[_AuctionID]);
        } else if (ModSemiAutarkFrequencyFee == true){
            FrequencyFee = fee.SemiAutarkFrequencyFee(_amount, checkLabel(_label), Frequencies[_AuctionID]);
        } else{
            FrequencyFee = 0;
        }
        
        if (ModAutarkVoltageFee == true){
            VoltageFee = fee.AutarkVoltageFee(_amount, checkLabel(_label),_AuctionID, register.getCircuit(_address));
        } else if (ModSemiAutarkVoltageFee == true){
            VoltageFee = fee.SemiAutarkVoltageFee(_amount, checkLabel(_label),_AuctionID, register.getCircuit(_address));
        } else{
            VoltageFee = 0;
        }
        
        reward = _amount *  MCPs[_AuctionID] + FrequencyFee + VoltageFee;
        
        if (checkLabel(_label) == 0){
            coin.changeCoinBalance(_address, reward);
            emit Transfer(_address,_amount, MCPs[_AuctionID], reward, FrequencyFee, VoltageFee,0,1,coin.getCoinBalance(_address));
        } else if (checkLabel(_label) == 1){
            coin.changeCoinBalance(_address, -reward);
            emit Transfer(_address, _amount, MCPs[_AuctionID], -reward, FrequencyFee, VoltageFee,0,1,coin.getCoinBalance(_address));
        }
        
        coin.changeCoinBalance(register.getTrafoFrequencyAddr(trafo), FrequencyFee);
        coin.changeCoinBalance(register.getTrafoVoltageAddr(trafo), VoltageFee);
    }
    
    function outerTransferMoney(uint256 _AuctionID, uint32 _amount, uint8 _label, address _address) private{
        int reward;
        int64 CongestionFee;
        int FrequencyFee;
        int VoltageFee;
        
        if (ModCongestionFee == true){
            CongestionFee = int32(_amount) * fee.CongestionFee(checkLabel(_label));
        }else{
            CongestionFee = 0;
        }
        
        if (ModAutarkFrequencyFee == true){
            FrequencyFee = fee.AutarkFrequencyFee(_amount, checkLabel(_label), Frequencies[_AuctionID]);
        } else if (ModSemiAutarkFrequencyFee == true){
            FrequencyFee = fee.SemiAutarkFrequencyFee(_amount,checkLabel(_label), Frequencies[_AuctionID]);
        } else{
            FrequencyFee = 0;
        }
        
        if (ModAutarkVoltageFee == true){
            VoltageFee = fee.AutarkVoltageFee(_amount, checkLabel(_label),_AuctionID, register.getCircuit(_address));
        } else if (ModSemiAutarkVoltageFee == true){
            VoltageFee = fee.SemiAutarkVoltageFee(_amount, checkLabel(_label),_AuctionID, register.getCircuit(_address));
        } else{
            VoltageFee = 0;
        }
        
        
        if (checkLabel(_label) == 0){
            reward = _amount *  GridPriceBuy - CongestionFee + FrequencyFee + VoltageFee;
            coin.changeCoinBalance(_address, reward); 
            coin.changeCoinBalance(register.getTrafoAddr(trafo), _amount *  -GridPriceBuy); //  substract the same amount from the Trafo Owner!
            emit Transfer(_address, _amount, GridPriceBuy, reward, FrequencyFee, VoltageFee, CongestionFee,2,coin.getCoinBalance(_address));
        } else if (checkLabel(_label) == 1){
            reward = _amount *  GridPriceSell + CongestionFee + FrequencyFee + VoltageFee;
            coin.changeCoinBalance(_address, -reward); 
            coin.changeCoinBalance(register.getTrafoAddr(trafo), _amount *  GridPriceSell); // add the same amount to the Trafo Owner!
            emit Transfer(_address, _amount, GridPriceSell, -reward, FrequencyFee, VoltageFee, CongestionFee,2,coin.getCoinBalance(_address));
        }
        
        coin.changeCoinBalance(register.getTrafoCongestionAddr(trafo), CongestionFee);
        coin.changeCoinBalance(register.getTrafoFrequencyAddr(trafo), FrequencyFee);
        coin.changeCoinBalance(register.getTrafoVoltageAddr(trafo), VoltageFee);
    }
    
    function escrow(uint256 _AuctionID) public { // needs to be changed to private as soon as implemented
        uint i;
        //uint32[] memory numberProCon= new uint32[](2); // had to put 2 variables into array bc of "stack too deep" exception
        
        // Determine if Produced or Consumed Amount is bigger
        uint32 amountProduced = 0;
        uint32 amountConsumed = 0;
        uint8 flag; // 0 -> More produced than consumed // 1 -> more consumed than produced // 2 -> tie
        
        for (i=0; i < participantsUsage[_AuctionID].length; i++){
            if (checkLabel(participantsUsage[_AuctionID][i].label) == 0){
                amountProduced = amountProduced + participantsUsage[_AuctionID][i].amount;
                //numberProCon[0]++;
            }
            if (checkLabel(participantsUsage[_AuctionID][i].label) == 1){
                amountConsumed = amountConsumed + participantsUsage[_AuctionID][i].amount;
                //numberProCon[1]++;
            }
        }
        if (amountProduced > amountConsumed){
            flag = 0;
        }else if (amountConsumed > amountProduced) {
            flag = 1;
        }else {
            flag = 2;
        }
        emit EscrowEvent(flag, amountProduced, amountConsumed,participantsUsage[_AuctionID].length, _AuctionID);
        
        // Set the Current Trafo Load
        if (flag == 0){
            fee.setCurrentTrafoLoad(amountProduced - amountConsumed, flag);
        }else if (flag == 1){
            fee.setCurrentTrafoLoad(amountConsumed - amountProduced, flag);
        }else {
            fee.setCurrentTrafoLoad(0, flag);
        }
        
        fee.setAmounts(amountProduced, amountConsumed);
        
        // Transfer Money according to the MCP, get difference from outer Cell if necessary
        uint32 amountDiff = 0;
        uint8 flagDiff = 2;
        for (i=0; i < participantsUsage[_AuctionID].length; i++){
            // Check if Bid Amount (amount2) or usage amount is bigger
            if (participantsUsage[_AuctionID][i].amount > participantsUsage[_AuctionID][i].amount2){
                // Actual Usage amount is bigger than Bid Amount
                amountDiff = participantsUsage[_AuctionID][i].amount - participantsUsage[_AuctionID][i].amount2;
                flagDiff = 0;
            }else if (participantsUsage[_AuctionID][i].amount < participantsUsage[_AuctionID][i].amount2){
                // Bid amount is bigger than Actual Usage Amount
                amountDiff = participantsUsage[_AuctionID][i].amount2 - participantsUsage[_AuctionID][i].amount;
                flagDiff = 1;
            }
            
            if (checkLabel(participantsUsage[_AuctionID][i].label) == 0){ // producers receive money
                if (participantsUsage[_AuctionID][i].price <= MCPs[_AuctionID]){ // sell within cell
                    if(flagDiff == 0){ // sell to outer cell the extra amount
                        innerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount2,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                        outerTransferMoney(_AuctionID,amountDiff,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                    }else if(flagDiff == 1){ // buy from outer cell the missing amount -> Consumer label
                        innerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount2,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                        outerTransferMoney(_AuctionID,amountDiff,18,participantsUsage[_AuctionID][i].xaddress);
                    }else{
                        innerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                    }
                } else { // sell outside of the cell
                    outerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                }
            }
            if (checkLabel(participantsUsage[_AuctionID][i].label) == 1){ // consumers pay money
               if (participantsUsage[_AuctionID][i].price >= MCPs[_AuctionID]){ // buy within cell
                    if(flagDiff == 0){ // buy extra amount from outer cell
                        innerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount2,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                        outerTransferMoney(_AuctionID,amountDiff,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                    }else if(flagDiff == 1){ // buy from outer cell the missing amount -> Consumer label
                        innerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount2,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                        outerTransferMoney(_AuctionID,amountDiff,8,participantsUsage[_AuctionID][i].xaddress);
                    }else{
                        innerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                    }
                } else { // buy outside of the cell
                    outerTransferMoney(_AuctionID,participantsUsage[_AuctionID][i].amount,participantsUsage[_AuctionID][i].label,participantsUsage[_AuctionID][i].xaddress);
                }
            }
        }
        
        //emit TrafoBalances(coin.getCoinBalance(register.getTrafoAddr(trafo)), coin.getCoinBalance(register.getTrafoCongestionAddr(trafo)), coin.getCoinBalance(register.getTrafoFrequencyAddr(trafo)), coin.getCoinBalance(register.getTrafoVoltageAddr(trafo))); 
        register.emitTrafoBalances(trafo, _AuctionID);
    }
    
    //Getter and Setter Functions
    function setContracts(address aRegister, address aCoin, address aFee) onlyOwner public{
        register = Register(aRegister);
        coin = FAUCoin(aCoin);
        fee = GridFee(aFee);
    }
    
    function setFrequency(uint256 _AuctionID, uint256 _frequency)  public{ //supposed to be onlyOwner but changed it for the simulation
        Frequencies[_AuctionID] = _frequency;
    }
    

    function getFrequency(uint256 _AuctionID) public constant returns (uint256){
        return Frequencies[_AuctionID];
    }
    
    function getTrafo() public constant returns (uint32) {
        return trafo;
    }
    
    function getMCP(uint256 _AuctionID) public constant returns (uint64) {
        return MCPs[_AuctionID];
    }
    
    function getAuctionID() public constant returns (uint256){
        return AuctionID;
    }

    //Sort Functions
    /*function sort(Details[] data) public returns(Details[]) {
       quickSort(data, int(0), int(data.length - 1));
       return data;
    }
    
    function quickSort(Details[] memory arr, int left, int right) internal{
        int i = left;
        int j = right;
        if(i==j) return;
        uint pivot = arr[uint(left + (right - left) / 2)].price;
        while (i <= j) {
            while (arr[uint(i)].price < pivot) i++;
            while (pivot < arr[uint(j)].price) j--;
            if (i <= j) {
                (arr[uint(i)], arr[uint(j)]) = (arr[uint(j)], arr[uint(i)]);
                i++;
                j--;
            }
        }
        if (left < j)
            quickSort(arr, left, j);
        if (i < right)
            quickSort(arr, i, right);
    }*/
}

//@author: Matthias Seidl
pragma solidity ^0.4.23;

import "browser/Register.sol";





contract GridFee{
  
    //Variables
    address public owner;
    
    Register register;
    
    uint32 trafo;
    uint32 currentTrafoLoad;
    uint8 trafoFlag;
    uint32 amountProduced;
    uint32 amountConsumed;
    //uint32 amountProducedF;
    //uint32 amountConsumedF;
    
    
    uint8 constant CongestionMaxLevelOne = 50;
    uint8 constant CongestionMaxLevelTwo = 80;
    uint8 constant CongestionLevelRateOne = 0;
    uint8 constant CongestionLevelRateTwo = 10;
    uint8 constant CongestionLevelRateThree = 25;
    
    uint8 constant FrequDiffMaxLevelOne = 80; // 0,08 Hz Abweichung
    uint8 constant FrequDiffMaxLevelTwo = 140; //0,14 Hz Abweichung
    uint8 constant FrequLevelRateOne = 0;
    uint8 constant FrequLevelRateTwo = 10;
    uint8 constant FrequLevelRateThree = 25;
    
    uint32 constant VoltDiffMaxLevelOne = 500; // 5V Abweichung
    uint32 constant VoltDiffMaxLevelTwo = 1000; // 10V Abweichung
    uint8 constant VoltLevelRateOne = 5;
    uint8 constant VoltLevelRateTwo = 10;
    uint8 constant VoltLevelRateThree = 15;
    
    mapping (address =>bool) ContractAddress;
    mapping (uint256 => mapping(uint8 => VoltageReg)) VoltageDir;
    
    //Events
    event showCongestionFee(uint32 _currentTrafoLoad, uint32 _MaxTrafoLoad, int _congestionFee, int usage);
    event showFrequencyFee(uint256 frequDiff, int fee, uint32 amount, uint8 reallabel, uint256 Frequency);
    //event showSemiAutarkFrequencyFee(uint256 frequDiff, int fee,uint16 amount, uint8 reallabel);
    event showVoltageFee(int fee,uint32 amount, uint8 reallabel, uint64 voltdiff, uint32 voltlevel, uint256 AuctionID, uint8 circuit, bool direction);
    event test(uint64 ratio, uint32 amountProduced, uint8 level);
    event EvenVoltReg(uint32 _voltage, uint256 _AuctionID, address sender, uint64 _diff, bool direction);
    
    //Structs
    struct VoltageReg {
        uint64 diff;
        bool direction; // True is high voltage (>230V) False is low voltage (<230V)
    }
    
    //Modifiers
    modifier onlyOwner(){
		require(msg.sender == owner);
		_;
	}
	
	modifier onlyValidContract(){
	    require(ContractAddress[msg.sender]);
        _;  
	}
    
    //Constructor
    constructor() public{
        owner = msg.sender;
        trafo = 9311;
    }
    
    //special Functions
    function CongestionFee(uint8 _reallabel) public returns (int32){
        int32 congestionFee;
        int usage = ((uint32(currentTrafoLoad) * 100) / uint32(register.getTrafoLoad(trafo)));
		//int usage = currentTrafoLoad / register.getTrafoLoad(trafo) * 100;
        if (usage < CongestionMaxLevelOne){
            congestionFee = CongestionLevelRateOne;
        }else if (usage < CongestionMaxLevelTwo){
            congestionFee = CongestionLevelRateTwo;
        }else{
            congestionFee = CongestionLevelRateThree;
        }
        emit showCongestionFee(currentTrafoLoad, register.getTrafoLoad(trafo), congestionFee, usage);
        
        if (_reallabel == 0){ //producer
            if (trafoFlag == 1){ // zu viel konsumiert
                congestionFee = -congestionFee;
            }
        }else if (_reallabel == 1) { //consumer
            if (trafoFlag == 0){ // zu viel produziert
                congestionFee = -congestionFee;
            }
        }
        return congestionFee;
    }
    
    function AutarkFrequencyFee(uint32 _amount, uint8 _reallabel, uint256 _Frequency) public returns (int){
        uint256 frequDiff; //reicht eigentlich wenn sie einmal berechnet wird -> kann ausgelagert werden und nach SetFrequency aufgerufen werden und dann global gespeichert.
        int fee;
        int64 ratio;
        if (_Frequency > 50000){ // Consumers get incentivized
            frequDiff = _Frequency - 50000;
            if (_reallabel == 0){ // producers pay
                fee = _amount * FrequencyLevel(frequDiff);
                fee = -fee; // minus bc it has to be payed
            } else if (_reallabel == 1){ //consumers receive
                ratio = (uint32(_amount) * 1000) / uint32(amountConsumed);
                fee = ratio * amountProduced * FrequencyLevel(frequDiff) / 1000;
                fee = -fee; // minus bc consumer has to pay less
            }
        }else{ // Producers get incentivized
            frequDiff = 50000 - _Frequency;
            if (_reallabel == 0){ // producers receive
                ratio = _amount *1000 / amountProduced;
                fee = ratio * amountConsumed * FrequencyLevel(frequDiff) / 1000;
            } else if (_reallabel == 1){ //consumers pay
                fee = _amount * FrequencyLevel(frequDiff);
            }
        }
        //emit showAutarkFrequencyFee(frequDiff, fee, _amount, _reallabel);
        emit showFrequencyFee(frequDiff, fee, _amount, _reallabel, _Frequency);
        return fee;
    }
    
    function SemiAutarkFrequencyFee(uint32 _amount, uint8 _reallabel, uint256 _Frequency) public returns (int){
        uint256 frequDiff;
        int fee;
        if (_Frequency > 50000){ // Consumers get incentivized
            frequDiff = _Frequency - 50000;
            fee = FrequencyLevel(frequDiff) * _amount;
            if (_reallabel == 0){ // producers pay -> gets paid less -> fee negative
                fee = -fee;
            } else if (_reallabel == 1){ //consumers receive -> pays less -> fee negative
                fee = -fee;
            }
        }else { // Producers get incentivized
            frequDiff = 50000 - _Frequency;
            fee = FrequencyLevel(frequDiff) * _amount;
            /*if (_reallabel == 0){ // producers receive -> gets paid more -> fee positive

            } else if (_reallabel == 1){ //consumers pay -> pays more -> fee positive

            }*/
        }
        //emit showSemiAutarkFrequencyFee(frequDiff, fee, _amount, _reallabel);
        emit showFrequencyFee(frequDiff, fee, _amount, _reallabel, _Frequency);
        return fee;
    }
    
    function AutarkVoltageFee(uint32 _amount, uint8 _reallabel, uint256 _AuctionID, uint8 _circuit) public returns (int){
        int fee;
        uint64 ratio;
        if (VoltageDir[_AuctionID][_circuit].direction == true){ // Consumers get incentivized
            if (_reallabel == 0){ // producers pay
                fee = _amount * VoltageLevel(VoltageDir[_AuctionID][_circuit].diff);
                fee = -fee; // minus bc it has to be payed
            } else if (_reallabel == 1){ //consumers receive
                ratio = (uint32(_amount) * 1000) / uint32(amountConsumed);
                fee = ratio * amountProduced * VoltageLevel(VoltageDir[_AuctionID][_circuit].diff) / 1000;
                fee = -fee; // minus bc consumer has to pay less
            }
        }else{ // Producers get incentivized
            if (_reallabel == 0){ // producers receive
                ratio = _amount *1000 / amountProduced;
                fee = ratio * amountConsumed * VoltageLevel(VoltageDir[_AuctionID][_circuit].diff) / 1000;
            } else if (_reallabel == 1){ //consumers pay
                fee = _amount * VoltageLevel(VoltageDir[_AuctionID][_circuit].diff);
            }
        }
        emit showVoltageFee( fee, _amount, _reallabel, VoltageDir[_AuctionID][_circuit].diff, VoltageLevel(VoltageDir[_AuctionID][_circuit].diff), _AuctionID, _circuit, VoltageDir[_AuctionID][_circuit].direction);
        return fee;
    }
    
    function SemiAutarkVoltageFee(uint32 _amount, uint8 _reallabel, uint256 _AuctionID, uint8 _circuit) public returns (int){
        int fee;
        fee = VoltageLevel(VoltageDir[_AuctionID][_circuit].diff) * _amount;
        
        if (VoltageDir[_AuctionID][_circuit].direction == true){ // Consumers get incentivized
            if (_reallabel == 0){ // producers pay -> gets paid less -> fee negative
                fee = -fee;
            } else if (_reallabel == 1){ //consumers receive -> pays less -> fee negative
                fee = -fee;
            }
        }/*else { // Producers get incentivized
            if (_reallabel == 0){
                
            }else if (_reallabel == 1){
                
            }
        }*/
        
        emit showVoltageFee( fee, _amount, _reallabel, VoltageDir[_AuctionID][_circuit].diff, VoltageLevel(VoltageDir[_AuctionID][_circuit].diff), _AuctionID, _circuit, VoltageDir[_AuctionID][_circuit].direction);
        return fee;
    }
    
    function FrequencyLevel(uint256 _frequDiff) public pure returns (uint8){
        if (_frequDiff < FrequDiffMaxLevelOne){
            return FrequLevelRateOne;
        }else if (_frequDiff < FrequDiffMaxLevelTwo){
            return FrequLevelRateTwo;
        }else {
            return FrequLevelRateThree;
        }
    }
    
    function VoltageLevel(uint64 _voltDiff) public pure returns (uint8){
        if (_voltDiff < VoltDiffMaxLevelOne){
            return VoltLevelRateOne;
        }else if (_voltDiff < VoltDiffMaxLevelTwo){
            return VoltLevelRateTwo;
        }else {
            return VoltLevelRateThree;
        }
    }
    
    function RegisterVoltage(uint8 _circuit, uint32 _voltage, uint256 _AuctionID) onlyValidContract public {
        uint64 _diff;
        //int64 val = _voltage - 23000;
        bool direction;
        
        if (_voltage > 23000){
            _diff = uint64(_voltage - 23000);
            direction = true;
        }else{
            _diff = uint64(23000 - _voltage);
            direction = false;
        }
        
        /*
        if (val > 0){
            _diff = uint64(val);
            direction = true;
        }else{
            _diff = uint64((-1 * val));
            direction = false;
        }*/
        
        // if difference of this node is bigger than the oldest highest difference then overwrite VoltageDir
        if (VoltageDir[_AuctionID][_circuit].diff < _diff){
            VoltageDir[_AuctionID][_circuit] = VoltageReg (_diff, direction);
            emit EvenVoltReg(_voltage, _AuctionID, msg.sender, _diff, direction);
        }
    }
    
    //Getter and Setter Functions
    function setContractAddress(address _contract, bool _tf) public onlyOwner{
        ContractAddress[_contract] = _tf;
    }
    
    function setRegister(address addr) onlyOwner public{ 
        register = Register(addr); 
    }
    
    function setCurrentTrafoLoad(uint32 _currentLoad, uint8 flag) onlyValidContract public{
        currentTrafoLoad = _currentLoad;
        trafoFlag = flag;
    }
    
    function setAmounts(uint32 _amountProduced, uint32 _amountConsumed) onlyValidContract public {
        amountProduced = _amountProduced;
        amountConsumed = _amountConsumed;
        //amountProducedF = _amountProduced;
        //amountConsumedF = _amountConsumed;
    }
}






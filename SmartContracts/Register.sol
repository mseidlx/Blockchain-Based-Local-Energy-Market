//@author: Matthias Seidl
pragma solidity ^0.4.23;

import "browser/FAUCoin.sol";





contract Register{
  
    //Variables
    address public owner;
  
    FAUCoin coin;
  
    mapping (address => Details) AddressMapping;
    mapping (address => DetailsTrafo) TrafoMapping;
    mapping (uint32 => address) Trafos; 
    
    //Events
    event newRegistered(address paymentAddress);
    event TrafoBalances(int BalanceGrid, int BalanceCongestion, int BalanceFrequency, int BalanceVoltage, uint256 AuctionID);
    
    //Structs
    struct Details {
        uint32 trafo;
        uint8 circuit; 
        uint8 label; //0:PV, 1:Wind, 2:CCP, 3:CHP, 4:Coal, 5:battery+, 10: battery-, 11:Consumer, 20:DNO
    }
    
    struct DetailsTrafo {
        address addrCongestion;
        address addrFrequency;
        address addrVoltage;
        uint32 trafo;
        uint32 maxLoad; 
    }
    
    //Modifiers
    modifier onlyOwner(){
		require(msg.sender == owner);
		_;
	}
    
    modifier onlyAddressOwner (address _address){
        require (msg.sender == _address);
        _;
    }
    
    //Constructor
    constructor() public{
        owner = msg.sender;
    }
    
    //special Functions
    function addParticipant(address _address, uint32 _trafo, uint8 _circuit, uint8 _label) public { //for implementation this should be an onlyOwner function
        AddressMapping[_address] = Details(_trafo, _circuit, _label);
        emit newRegistered(_address);
        coin.changeCoinBalance(_address,500000000);
    }
    
    function addTrafo (address _addressGrid,address _addressCong,address _addressFreq,address _addressVolt, uint32 _trafo, uint32 _maxLoad) public onlyOwner{
        Trafos[_trafo]=_addressGrid;
        TrafoMapping[_addressGrid] = DetailsTrafo(_addressCong,_addressFreq,_addressVolt,_trafo, _maxLoad);
        coin.changeCoinBalance(_addressGrid,100000000);
        coin.changeCoinBalance(_addressCong,100000000);
        coin.changeCoinBalance(_addressFreq,100000000);
        coin.changeCoinBalance(_addressVolt,100000000);
    }
    
    //Getter and Setter Functions
    function setFAUCoin(address addr) onlyOwner public{ 
        coin = FAUCoin(addr); 
    }
    
    function setLabel(address _address, uint8 _label) public onlyAddressOwner(_address){
        AddressMapping[_address].label = _label;
    }

    function getLabel(address _account) public constant returns (uint8) {
        return AddressMapping[_account].label;
    }

    function getCircuit(address _account) public constant returns (uint8) {
        return AddressMapping[_account].circuit;
    }

    function getTrafoID(address _account) public constant returns (uint32) {
        return AddressMapping[_account].trafo;
    }
    
    function getTrafoAddr(uint32 _tid) public constant returns (address) {
        return Trafos[_tid];
    }
    
    function getTrafoLoad(uint32 _tid) public constant returns (uint32) {
        return TrafoMapping[Trafos[_tid]].maxLoad;
    }
    
    function getTrafoCongestionAddr(uint32 _tid) public constant returns (address) {
        return TrafoMapping[Trafos[_tid]].addrCongestion;
    }
    
    function getTrafoFrequencyAddr(uint32 _tid) public constant returns (address) {
        return TrafoMapping[Trafos[_tid]].addrFrequency;
    }
    
    function getTrafoVoltageAddr(uint32 _tid) public constant returns (address) {
        return TrafoMapping[Trafos[_tid]].addrVoltage;
    }
    
    function emitTrafoBalances(uint32 _tid, uint256 _AuctionID) public{
        emit TrafoBalances(coin.getCoinBalance(getTrafoAddr(_tid)), coin.getCoinBalance(getTrafoCongestionAddr(_tid)), coin.getCoinBalance(getTrafoFrequencyAddr(_tid)), coin.getCoinBalance(getTrafoVoltageAddr(_tid)), _AuctionID); 
    }
}






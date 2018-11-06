//@author: Matthias Seidl
pragma solidity ^0.4.23;







contract FAUCoin{
    
    //Variables
    address public owner;
    
    mapping (address => int) FAUCoinBalance;
    mapping (address =>bool) ContractAddress;
    
    //Events
    event Transfer(address indexed _from, address indexed _to, uint32 _value);
    event Balance(address xaddress, int _balance);
    
    //Modifiers
    modifier onlyOwner(){
		require(msg.sender == owner);
		_;
	}
    
    modifier onlyValidContract() {
        require(ContractAddress[msg.sender]);
        _;
    }
    
    //Constructor
    constructor() public {
        owner = msg.sender;
    }
    
    //special Functions
    function changeCoinBalance(address _account, int _change) public onlyValidContract {
        FAUCoinBalance[_account] += _change; // hier müsste eig noch eine Überprüfung hin ob man nach dem Change noch im Plus ist...
        emit Balance (_account, FAUCoinBalance[_account]);
    }
    
    function transfer(address _to, uint32 _amount) public returns (bool success) {
        if ((uint32(FAUCoinBalance[msg.sender]) >= _amount) && (_amount > uint16(0)))  {
            FAUCoinBalance[msg.sender] -= int32(_amount);
            FAUCoinBalance[_to] += int32(_amount);
            emit Transfer(msg.sender, _to, _amount);
            return true;
        }
    }
    
    //Getter and Setter Functions
    function setContractAddress(address _contract, bool _tf) public onlyOwner{
        ContractAddress[_contract] = _tf;
    }
    
    function getCoinBalance(address _address) view public returns (int) {
        return FAUCoinBalance[_address];
    }
}

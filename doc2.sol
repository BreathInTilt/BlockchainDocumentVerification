// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DocumentRegistry {
    struct Document {
        uint256 timestamp;
        address owner;
        bool isRegistered;
    }

    mapping(bytes32 => Document) public documentHashMap;
    address public owner;

    event DocumentRegistered(bytes32 indexed hash, address owner, uint256 timestamp);
    event RegistrationFeeChanged(uint256 newFee);

    uint256 public registrationFee;

    constructor(uint256 _registrationFee) {
        owner = msg.sender;
        registrationFee = _registrationFee;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not the owner");
        _;
    }

    modifier paysFee(uint256 _fee) {
        require(msg.value >= _fee, "Insufficient fee");
        _;
    }

    function registerDocument(bytes32 documentHash) public payable paysFee(registrationFee) {
        require(!documentHashMap[documentHash].isRegistered, "Document is already registered.");

        documentHashMap[documentHash] = Document({timestamp: block.timestamp, owner: msg.sender, isRegistered: true});
        emit DocumentRegistered(documentHash, msg.sender, block.timestamp);
    }

    function setRegistrationFee(uint256 _newFee) public onlyOwner {
        registrationFee = _newFee;
        emit RegistrationFeeChanged(_newFee);
    }

    function verifyDocument(bytes32 documentHash) public view returns (uint256, address) {
        Document memory doc = documentHashMap[documentHash];
        require(doc.isRegistered, "Document is not registered.");
        return (doc.timestamp, doc.owner);
    }

    function withdrawFees() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
}

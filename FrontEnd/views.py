from django.shortcuts import render, redirect
from .forms import DocumentForm
from .models import Document
from web3 import Web3
import hashlib
from decimal import Decimal, Context, setcontext

web3 = Web3(Web3.HTTPProvider('HTTP://127.0.0.1:8545'))

cct_bin = "0x8368DAcc6C9F6a1Df0732DF614b9d60D001CCFA2"
abi = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "hash",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "DocumentRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newFee",
                "type": "uint256"
            }
        ],
        "name": "RegistrationFeeChanged",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "documentHash",
                "type": "bytes32"
            }
        ],
        "name": "registerDocument",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_newFee",
                "type": "uint256"
            }
        ],
        "name": "setRegistrationFee",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_registrationFee",
                "type": "uint256"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [],
        "name": "withdrawFees",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            }
        ],
        "name": "documentHashMap",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "internalType": "bool",
                "name": "isRegistered",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "registrationFee",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "documentHash",
                "type": "bytes32"
            }
        ],
        "name": "verifyDocument",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

contract_abi = abi
contract_address = web3.to_checksum_address(cct_bin)
contract = web3.eth.contract(address=contract_address, abi=contract_abi)
web3.eth.defaultAccount = web3.eth.accounts[0]


def check_contract_is_operational():
    try:
        # Вызов функции контракта, которая не требует gas
        fee = contract.functions.registrationFee().call()
        return True, fee  # Контракт доступен, возвращаем True и значение fee
    except Exception as e:
        return False, str(e)  # Контракт не доступен, возвращаем False и описание ошибки


def get_file_hash(file):
    # Возможно, потребуется добавить более сложную логику для больших файлов

    hasher = hashlib.sha256()
    for chunk in file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


def check_file_exists_in_ganache(file_hash):
    # Удалите '0x', если он присутствует, и убедитесь, что длина строки равна 64 символам
    clean_hash = file_hash[2:] if file_hash.startswith('0x') else file_hash
    if len(clean_hash) != 64:
        raise ValueError("File hash must be a 64-characters long hexadecimal string")

    file_hash_bytes = bytes.fromhex(clean_hash)
    document_info = contract.functions.documentHashMap(file_hash_bytes).call()
    timestamp = document_info[0]
    return timestamp != 0  # Если timestamp не 0, значит документ уже зарегистрирован


def toHex(data):
    if isinstance(data, int):
        return hex(data)
    elif isinstance(data, bytes):
        return data.hex()
    else:
        raise TypeError("Unsupported data type for toHex function")


def toWei(number, unit):
    # Словарь с коэффициентами для различных единиц
    units = {
        'wei': 1,
        'kwei': 10**3,
        'mwei': 10**6,
        'gwei': 10**9,
        'szabo': 10**12,
        'finney': 10**15,
        'ether': 10**18
    }

    # Проверяем, что предоставленная единица действительна
    if unit not in units:
        raise ValueError("Unknown unit")

    # Используем точные десятичные вычисления
    setcontext(Context(prec=999))

    # Конвертируем число в десятичное и умножаем на коэффициент единицы
    wei_value = Decimal(number) * units[unit]
    return int(wei_value)


def register_file_in_ganache(file_hash):
    file_hash_bytes = bytes.fromhex(file_hash[2:]) if file_hash.startswith('0x') else bytes.fromhex(file_hash)
    transaction = contract.functions.registerDocument(file_hash_bytes).build_transaction({
        'from': web3.eth.defaultAccount,
        'value': toWei(0.01, 'ether'),  # Предполагаемая стоимость регистрации
        'gas': 200000,
        'gasPrice': toWei('50', 'gwei'),
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount),
    })
    # ВАЖНО: Замените 'YOUR_PRIVATE_KEY' на реальный приватный ключ. Будьте осторожны с безопасностью ключа.
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key='0x6b7952821c49860da55e3d85b4cb0b9576133ec3e7ab1288f9e671d11ee08925')

    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return toHex(tx_hash)


def home(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            new_doc = Document(upload=request.FILES['file'])

            # Получаем хэш файла
            file_hash = get_file_hash(request.FILES['file'])
            print("get_file_hash completed")
            # Проверяем, существует ли уже файл в Ganache
            if not check_file_exists_in_ganache(file_hash):
                print("check_file_exists completed")
                # Регистрируем файл в Ganache, если его нет
                new_doc.file_hash = get_file_hash(request.FILES['file'])  # Сохраняем хеш файла
                new_doc.save()
                tx_hash = register_file_in_ganache(file_hash)
                print("register_file_in_ganache completed")
                return redirect('home')
            else:
                # Обработка случая, когда файл уже зарегистрирован
                pass

    else:

        form = DocumentForm()

    documents = Document.objects.all()  # Получаем все документы
    return render(request, 'home.html', {'form': form, 'documents': documents})

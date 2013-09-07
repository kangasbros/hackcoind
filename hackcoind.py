"""hackcoind - bitcoind proxy with deterministic keys

Usage:
  hackcoind.py
  hackcoind.py ship <name> move <x> <y> [--speed=<kn>]
  hackcoind.py ship shoot <x> <y>
  hackcoind.py mine (set|remove) <x> <y> [--moored | --drifting]
  hackcoind.py (-h | --help)
  hackcoind.py --version

Options:
  -h --help     Show this screen.
  --version     Version
  --rebuild     Checks that wallet.dat of bitcoind has all the necessary keys, and adds them if they do not exist.

"""
from docopt import docopt

from jsonrpc import ServiceProxy
import simplejsonrpc as jsonrpc
from pprint import pprint
import leveldb
import simplejson as json

config = json.load(open('config.json'))

bitcoind = ServiceProxy(config["bitcoind_connection"])

# methodToCall = getattr(bitcoind, "getinfo")
# methodToCall()

chain_headers = leveldb.LevelDB('./chain_headers.db')
chain_data = leveldb.LevelDB('./chain_data.db')

LARGEST_POSSIBLE_SUBKEY = 2147483647

from pycoin.wallet import Wallet

print "Enter wallet passphrase:",
passphrase = raw_input()

my_prv = Wallet.from_master_secret(passphrase)
my_prv_key = my_prv.wallet_key(as_private=True)
my_pub_key = my_prv.wallet_key(as_private=False)
my_pub = Wallet.from_wallet_key(my_pub_key)
print "Master pub key", my_pub_key

try:
    master_pub_key = chain_headers.Get("pub_key")
    if master_pub_key != my_pub_key:
        raise Exception("Error: db master pub key differs from input key.")
except KeyError:
    chain_headers.Put('pub_key', my_pub_key)

try:
    master_pub_key = chain_data.Get("pub_key")
    if master_pub_key != my_pub_key:
        raise Exception("Error: db master pub key differs from input key.")
except KeyError:
    chain_data.Put('pub_key', my_pub_key)

print "Trying to connect bitcoind..."
print bitcoind.getinfo()
print "success"

def getnextfromchain(*arg):
    if len(arg) == 0:
        raise Exception("Can't be called without key path!")
    keychain_path = "/".join((str(i) for i in arg))
    try:
        key_count = int(chain_headers.Get(keychain_path))
        chain_headers.Put(keychain_path, str(key_count+1))
    except KeyError:
        chain_headers.Put(keychain_path, str(1))
        key_count = 0
    subkey_path = keychain_path+"/"+str(key_count)
    bitcoin_address = my_pub.subkey_for_path(subkey_path).bitcoin_address()
    wif = my_prv.subkey_for_path(subkey_path).wif(compressed=False)
    try:
        retrieved_address = int(chain_data.Get(subkey_path))
        if retrieved_address != bitcoin_address:
            raise Exception("Double error! Address already in database, and it is wrong!")
        raise Exception("Address shouldn't be in database! Perhaps you have wrong chain_data.db?")
    except KeyError:
        chain_data.Put(subkey_path, bitcoin_address)
    bitcoind.importprivkey(wif, subkey_path, False)
    print keychain_path, subkey_path, bitcoin_address
    return bitcoin_address

getnextfromchain(0,0)
getnextfromchain(0,0)
getnextfromchain(0,0)
getnextfromchain(0,0)

pprint(retrieved_chains)

getnextfromchain(0)
getnextfromchain(0)
getnextfromchain(0)
getnextfromchain(0)

pprint(retrieved_chains)

getnextfromchain(5,3)
getnextfromchain(5,3)
getnextfromchain(5,3)

# pprint(retrieved_chains)

def genewaddress(*arg):
    return "getnewaddress"
    # return from chain 0,0 if no chain specified
    if len(arg) == 0:
        if len(retrieved_addresses) == 0:
            return getnextfromchain(0, 0)
    else:
        # limit chains "0/1-N" for general usage
        if len(arg) == 2 and arg[0]==0:
            raise Exception("These addresses are reserved for general requests.")
        return getnextfromchain(arg)

def add(a, b):
    return a + b

def default(*arg, **kwargs):
    return "hello jsonrpc"

class MyJsonrpcHandler(jsonrpc.JsonrpcHandler):
    """define your own dispatcher here"""
    def dispatch(self, method_name):
        if method_name == "genewaddress":
            return genewaddress
        else:
            methodToCall = getattr(bitcoind, method_name)
            return methodToCall


# class MyJsonrpcHandler(jsonrpc.JsonrpcHandler):
#     """define your own dispatcher here"""
#     def dispatch(self, method_name):
#         if method_name == "genewaddress":
#             return genewaddress
#         else:
#             methodToCall = getattr(bitcoind, method_name)
#             return methodToCall


def application(environ, start_response):
    # assert environ["REQUEST_METHOD"] = "POST"
    content_length = int(environ["CONTENT_LENGTH"])

    # create a handler
    h = MyJsonrpcHandler()

    # fetch the request body
    request = environ["wsgi.input"].read(content_length)

    # pass the request body to handle() method
    result = h.handle(request)

    #log
    environ["wsgi.errors"].write("request: '%s' | response: '%s'\n" % (request, result))

    start_response("200 OK", [])
    return [result]

from wsgiref.simple_server import make_server
rpcserver = make_server('', 7999, application)
print "Serving on port 7999..."
rpcserver.serve_forever()
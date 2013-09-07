import simplejsonrpc as jsonrpc

server = jsonrpc.Server("http://localhost:7999")
print server.getnewaddress()
print server.getinfo()
hackcoind is simple proxy for bitcoind. Essentially the goal is to replace bitcoind key management with deterministic keys, so that no wallet.dat recovery is needed.

depends (have to be setup separately):
git+git://github.com/jgarzik/python-bitcoinrpc
pycoin
leveldb
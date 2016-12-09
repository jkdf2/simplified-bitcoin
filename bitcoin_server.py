from flask import Flask, request
from redis import StrictRedis
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import jsonpickle
import codecs
import hashlib
server = Flask(__name__)
redis = StrictRedis(host='localhost', port=6379)

@server.before_first_request
def create_genesis_block():
    redis.flushall()

    sk = SigningKey.generate(curve=SECP256k1)
    redis.set('server_private_key', sk.to_string())

    vk = sk.get_verifying_key()
    redis.set('server_public_key', vk.to_string())

    # don't need to the private key anymore
    del sk

    # introduce 50 coins into the ecosystem
    transaction = [(vk.to_string(), 50)]
    genesis_block = (0x0, transaction)

    # start the blockchain
    redis.rpush("blockchain", jsonpickle.encode(genesis_block))


@server.route('/free_money/', methods=['PUT'])
def distribute_money():
    """
    Gives out free coins if they are available.

    Limited time offer!
    """
    user_data  = jsonpickle.decode(request.data.decode("utf-8"))
    to_address = user_data[0]
    n          = user_data[1]

    blockchain = redis.lrange("blockchain", 0, redis.llen("blockchain"))
    found = False
    for block in reversed(blockchain):
        block = jsonpickle.decode(block.decode("utf-8"))
        transactions = block[1]
        for public_key, amt in transactions:
            if public_key == redis.get('server_public_key') and amt >= n:
                found = True

                # split the transaction if necessary
                if amt != n:
                    print("Splitting up the transaction to send.")
                    pass
                    # split
                    # TODO
                else:
                    print("Can distribute money in a single transaction.")
                    transactions = [(to_address, n)]

    if not found:
        return "Not Found", 416  # invalid range

    if construct_block(redis.get('server_public_key'), transactions):
        return "Created", 201  # created
    else:
        # uh oh
        return "Server Error", 500  # server error!

# TODO:
# Implement a send_money endpoint that will send X coins from a given public
# key to another public key, after a successful signature verification.

def construct_block(from_address, transactions):
    """
    Creates a new block with the given tx info and attaches it to the end of
    the blockchain. Returns True on success.
    """
    # TODO: Take in the specific block index and transaction index within that block.
    # We would verify from that transact to the latest block to ensure that a
    # double-spend is not occuring.
    
    total = sum(amt for _, amt in transactions)
    blockchain = redis.lrange("blockchain", 0, redis.llen("blockchain"))

    # Verification step:
    # Look for a previous transaction that sums up to this amount, given the
    # public key.
    found = False
    for block in reversed(blockchain):
        block = jsonpickle.decode(block.decode("utf-8"))
        transactions_in_block = block[1]
        for public_key, amt in transactions_in_block:
            if public_key == from_address and amt == total:
                found = True

        if found:
            break
        
    if not found:
        print("Did not find public_key {} in blockchain totaling {}".format(from_address, total))
        return False

    # Preserve the integretiy of the blockchain by adding the hash of the
    # previous block to this block.
    # Note that in a full implementation, this hash would have to be
    # less than a certain amount in order to make it take several minutes or
    # more to solve this puzzle and provide proof of work.
    prev_hash = hashlib.sha256(blockchain[len(blockchain) - 1]).digest()
    block = (prev_hash, transactions)
    redis.rpush("blockchain", jsonpickle.encode(block))
    return True

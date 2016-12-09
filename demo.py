#!/usr/bin/python3
import requests
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import codecs
import jsonpickle

def run_demo():
    alice = User("alice")
    recieve  = (alice.public_key, 50)
    r = requests.put("http://localhost:5000/free_money/", data=jsonpickle.encode(recieve))
    if r.status_code == 201:
        print("Alice successfully requested 50 bitcoins from the server.")
    else:
        print("Alice could not get 50 bitcoins from the server.")

class User():
    def __init__(self, name):
        self.name = name
        sk = SigningKey.generate(curve=SECP256k1)
        vk = sk.get_verifying_key()
        self._private_key = sk.to_string()
        self.public_key   = vk.to_string()

if __name__ == "__main__":
    run_demo()

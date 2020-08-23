
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
from Crypto.PublicKey import RSA

# Part 1 - Building a Blockchain

class Blockchain:
#chain(emptylist) , farmer_details(emptylist), nodes(set), create_block(function to create the genesis block)
    def __init__(self):
        self.chain = []
        self.farmer_details = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
#It creates a dictionary block which contains     index(length of chain+1),timestamp( by using the module datetime),
#Proof( passes as parameter),previous_hash(passed as parameter),
#Farmer_details(from self) and append this to the chain.
 
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'farmer_details': self.farmer_details}
        self.farmer_details = []
        self.chain.append(block)
        return block
#It returns the last block of the chain.
    def get_previous_block(self):
        return self.chain[-1]
#It runs a lop and check if hash of new proof^2- previous proof^2 contains 4 leading zeroes. 
#if yes,then it returns the new proof otherwise increment the new proof by 1 and iterates again.
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
#- It returns the hash of the block using sha256   
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
#It iterates a loop from 0 to chain length and check if hash of the block is same as returned by the hash function, 
#then it checks if hash of the proof of current block^2-proof of previous block^2 contains 4 leading zeroes or not.
# if no, then chain is not valid.  
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
#- It creates the private key using the RSA.generate(1024),then creates the public key,
# hash of transaction(it is the hash of the sum of hashes of the name,crop_name,quantity,rate),
#data( it is the hash of the transaction in the int form),
#signature( it is created by raising the data to the power of privatekey.d%privatekey.n).
# Then it append a dictionary containing all these information in the hash format to the chain farmer_details 
#and returns the index of the new block.   
    def add_farmerdetails(self, name, crop_name, quantity,rate):
        privatekey = RSA.generate(1024)  
        publickey = privatekey.publickey()  
        hash_of_transaction=hashlib.sha256((hashlib.sha256(name.encode()).hexdigest()+hashlib.sha256(crop_name.encode()).hexdigest()+hashlib.sha256(str(quantity).encode()).hexdigest()+hashlib.sha256(str(rate).encode()).hexdigest()).encode()).hexdigest()
        data=int(hash_of_transaction,16)
        signature=pow(data,privatekey.d,privatekey.n)
        self.farmer_details.append({'name_of_farmer': hashlib.sha256(name.encode()).hexdigest(),
                                  'crop_name':  hashlib.sha256(crop_name.encode()).hexdigest(),
                                  'quantity_inkg':  hashlib.sha256(str(quantity).encode()).hexdigest(),
                                  'rate_perkg': hashlib.sha256(str(rate).encode()).hexdigest(),
                                  'hash_of_transaction': hash_of_transaction,
                                  'signature': signature
                                  })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
#It takes the url using urlparse of the address and then adds this to the set nodes in the self.
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
#It access all the nodes in the set nodes and then iterates a loop to get their chain length using get_chain (to be described)
# and replaces the current chain with the longest chain of all the nodes.   
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5001
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
#- It access the previous block by calling the function get_previous_block(), 
#then access the previous proof by previous_block[‘proof’],
#then it creates a new proof by using the function proof_of_work(‘previous_proof’), 
#then it finds the hash of the previous block by using the function blockchain.hash(previous_block),
# then calls the function create_block( proof,previous_hash),then finds the hash of this block.
# It creates a response containing all the details of the new block,jsonify it and returns it.
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    #blockchain.add_transaction(sender = node_address, receiver = 'Hadelin', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    current_block=blockchain.get_previous_block()
    current_hash=blockchain.hash(current_block)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'farmer': block['farmer_details'],
                'current_hash': current_hash}
    return jsonify(response), 200

# Getting the full Blockchain
#- It creates an empty list chain_till_now, then iterates over all the blocks in the blockchain and find it’s hash 
#then check if the list farmer_details is empty or not, 
#if it is empty then it appends a dictionary containing the current block’s index,timestamp,proof,previous_hash, current_hash, farmer_details.
# If the farmer_details list is not empty then it first finds the length of the list farmer_details 
#then it iterates over the length of the list farmer_details and appends the hash of transaction 
# contained within the dictionary of the list farmer_details. Then it creates the hash of this appended hash. This is the merged hash.
# Then it creates a dictionary containing merged hash,index,timestamp,proof,previous_hash,farmer_details and current hash.
# Then, it appends this dictionary to the list chain till now.
# It then creates the response containing the chain till now and length of the blockchain,jasonifies it and returns it. 

@app.route('/print_chain',methods=['GET'])
def print_chain():
    chain_till_now =[]
    for xblock in blockchain.chain:
     xcurrent_hash=blockchain.hash(xblock) 
     if len(xblock['farmer_details'])==0:
      chain_till_now.append({'index': xblock['index'],
                'timestamp': xblock['timestamp'],
                'proof': xblock['proof'],
                'previous_hash': xblock['previous_hash'],
                'farmer': xblock['farmer_details'],
                'current_hash': xcurrent_hash})
     else:
      l=len(xblock['farmer_details'])
      sum=""
      l-=1
      while(l>=0):
       sum=xblock['farmer_details'][l]['hash_of_transaction']+sum
       l-=1
      chain_till_now.append({'Merged_hash': hashlib.sha256(sum.encode()).hexdigest(),
                'index': xblock['index'],
                'timestamp': xblock['timestamp'],
                'proof': xblock['proof'],
                'previous_hash': xblock['previous_hash'],
                'farmer': xblock['farmer_details'],
                'current_hash': xcurrent_hash})    
    response = {'chain': chain_till_now,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

#- It creats the response containing the blockchain.chain and its length,jasonifies it and returns it.   
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
#- It calls the function is_chain_valid and returns a string as response based on whether the chain is valid or not.
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
#It takes the input in Jason format and checks if all the keys in the farmer keys(name_of_farmer,crop_name,quantity_inkg, rate_perkg)  are available in the json file. 
#If no, It returns that some elements are missing
# otherwise it calls the function add_farmer_details by passing the farmer details in the json file as parameter and 
#returns the index of the block in which these details will be added.
@app.route('/add_farmerdetails', methods = ['POST'])
def add_farmer_details():
    json = request.get_json()
    farmer_keys = ['name_of_farmer', 'crop_name', 'quantity_inkg','rate_perkg']
    if not all(key in json for key in farmer_keys):
        return 'Some elements of the farmer_details are missing', 400
    index = blockchain.add_farmerdetails(json['name_of_farmer'], json['crop_name'], json['quantity_inkg'], json['rate_perkg'])
    response = {'message': f'These details will be added to Block {index}'}
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
#It takes a Jason file as request and first check if it contains any node or not.
# If it contains the nodes then it calls the function blockchain.add_node .
#Then it returns the list of blockchain.nodes as response.
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The puspesh Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
#-   It calls the function blockcain.replace_chain. If the chain is replaced 
#it returns the response with a message that the nodes has the different chains so the chain has been replaced by the longest chain alongwith the blockchain.chain.
# Otherwise it returns the response with a message all good the chain is the longest one with the blockchain.chain .
#then it jsonify the response and returns it.
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5002)

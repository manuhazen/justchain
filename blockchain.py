import hashlib
import json
import requests

from urllib.parse import urlparse
from time import time
from uuid import uuid4

class Blockchain(object):
	def __init__(self):
		self.chain = []
		self.current_transactions = []
		self.nodes = set()

		# Create the genesis block
		self.create_new_block(previous_hash=1, proof=100)

	def register_node(self, address):
		"""
			Add a new node to the list of nodes

			address. Type: String. Address of the none. Eg: 'http://192.168.0.3:4000'
			return None
		"""

		parsed_url = urlparse(address)
		self.nodes.add(parsed_url.netloc)

	def valid_chain(self, chain):
		"""
		Determine if a given blockchain is valid

		chain. Type: list. A blockchain
		return. Type: boolean. True if valid, false if not
		"""

		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			print(f'{last_block}')
			print(f'{block}')
			print("\n-------------\n")

			# Check the hash of the block is correct
			if block['previous_hash'] != self.hash(last_block):
				return False

			# Check that the PoW is correct
			if not self.valid_proof(last_block['proof'], block['proof']):
				return False

			last_block = block
			current_index += 1
		return True


	def resolve_conflicts(self):
		"""
		This is our consensus algorithm, it resolve conflicts by
		replacing our chain with the longest one in the network

		return Boolean if our chain was replaced 
		"""

		neighbours = self.nodes
		new_chain = None

		# We're only looking for chains longers than ours
		max_length = len(self.chain)

		# Grab and verify the chains from all the nodes in our network
		for node in neighbours:
			response = requests.get(f'http://{node}/chain')

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				# check if the length is longer and the chain is valid
				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		# Replace our chain if we descovered a new, valid chain longer than ours
		if new_chain:
			self.chain = new_chain
			return True

		return False

	def create_new_block(self, proof, previous_hash=1):
		"""
			Create a new block in the Blockchain

			proof. Type: Integer. Proof of work algorithm.
			previous_hash. Type: String. Hash of the previous block. (Optional)

			return. Type: Dictionarie. New Block
		"""

		block = {
			'index': len(self.chain) + 1,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1]),
		}

		# Reseting the current list of transactions
		self.current_transactions = []

		# adding the block to the chain of blocks 
		self.chain.append(block)

		return block

	def new_transaction(self, sender, recipient, amount):
		"""
			Creates a new transaction to go into the next mined Block.

			sender. Type: String. Address of the Sender.
			recipient. Type: String. Address of the recipient.
			amount. Type: Integer. Amount of the transaction.

			This function return the index of the block that will hold this transaction
		"""
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount
		})

		return self.last_block['index'] + 1

	def proof_of_work(self, last_proof):
		"""
			Proof Algorithm:
			- Find a number p' such that hash (pp') contains leading 4 zeroes, where p is the previous
			- p is the previos proof, and p' is the new proof

			last_proof. Type: Integer
			return Integer
		"""

		proof = 0
		while self.valid_proof(last_proof, proof) is False:
			proof += 1

		return proof



	@staticmethod
	def valid_proof(last_proof, proof):
		"""
			Validates the proof: Does hash(last_proof, proof) contains leading 4 zeroes?

			last_proof. Type: Integer. Previous Proof.
			proof. Type: Integer. Current Proof.

			return a Boolean. True is correct, False is not.
		"""

		guess = f'{last_proof}{proof}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"


	@staticmethod
	def hash(block):
		"""
			Creates a SHA-256 hash of a Block

			block. Type: Dict. A block.
			return a string with the hash
		"""

		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	@property
	def last_block(self):
		return self.chain[-1]

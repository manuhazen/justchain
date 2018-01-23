from textwrap import dedent
from time import time
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

from blockchain import Blockchain

# Instantiate the node
app = Flask(__name__)

# Generate the address for this node
node_identifier = str(uuid4()).replace('-','')

# Instantiate the blockchain

justchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
	# Run the proof of work to get the next proof and mine the block
	last_block = justchain.last_block
	last_proof = last_block['proof']
	proof = justchain.proof_of_work(last_proof)

	# With the proof we can make a new transaction
	justchain.new_transaction(
		sender="0",
		recipient=node_identifier,
		amount=1
	)

	# Forge the new block and add a new one to the chain
	previous_hash = justchain.hash(last_block)
	block = justchain.create_new_block(proof, previous_hash)

	response = {
		'message': 'New block Forged',
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash']
	}


	return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	values = request.get_json()

	nodes = values.get('nodes')
	if nodes is None:
		return "Error: please supply a valid list of nodes", 400

	for node in nodes:
		justchain.register_node(node)

	response = {
		'message': 'New nodes have been added',
		'total_nodes': list(justchain.nodes),
	}

	return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	replaced = justchain.resolve_conflicts()

	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': justchain.chain
		}
	else:
		response = {
			'message': 'Our chain is authoratative',
			'chain': justchain.chain
		}

	return jsonify(response), 200
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	values = request.get_json()
	print(values)
	# Checking if the required fields are in the POST request
	required = ['sender', 'recipient', 'amount']
	if not all(k in values for k in required):
		return 'Missin values', 400

	# Creating a new transaction if exists all the fields
	index = justchain.new_transaction(values['sender'], values['recipient'], values['amount'])

	response = {'message': f'Transaction will be added to Block {index}'}
	return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
	response = {
		'chain': justchain.chain,
		'length': len(justchain.chain)
	}
	return jsonify(response), 200


if __name__ == '__main__':
	app.run(host='127.0.0.1', port=5000)
#!/usr/bin/env python3
"""
Test PureChain transaction methods
"""

import json
import time
import hashlib
import asyncio
from purechainlib import PureChain

# Configuration
NETWORK = "testnet"
PRIVATE_KEY = "742d620beac984c44bea9c3c8533b1d819a386a72ebd9bc3dcb47ee03d0034aa"

async def test_transaction():
    """Test transaction sending."""
    
    # Connect to PureChain
    print("Connecting to PureChain...")
    pc = PureChain(NETWORK)
    pc.connect(PRIVATE_KEY)
    print(f"Connected: {pc.address}")
    
    # Create test data
    data = {
        "record_id": "test_001",
        "content_hash": hashlib.sha256(b"test").hexdigest(),
        "timestamp": int(time.time())
    }
    data_hex = "0x" + json.dumps(data).encode().hex()
    
    print("\n1. Testing send with dict parameter...")
    try:
        tx_dict = {
            "to": "0x0000000000000000000000000000000000000001",
            "value": 0,
            "data": data_hex
        }
        result = await pc.send(to=tx_dict)
        print(f"   Success! Result: {result}")
        return result
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing simple send (value transfer)...")
    try:
        result = await pc.send(
            to="0x0000000000000000000000000000000000000001",
            value="0"
        )
        print(f"   Success! Result: {result}")
        # Could we attach data somehow?
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Testing web3.eth.send_transaction...")
    try:
        if hasattr(pc, 'web3'):
            tx = {
                'to': "0x0000000000000000000000000000000000000001",
                'value': 0,
                'data': data_hex,
                'from': pc.address
            }
            
            # Get nonce
            nonce = pc.web3.eth.get_transaction_count(pc.address)
            tx['nonce'] = nonce
            
            # Estimate gas
            try:
                gas = pc.web3.eth.estimate_gas(tx)
                tx['gas'] = gas
            except:
                tx['gas'] = 100000
            
            tx['gasPrice'] = pc.web3.eth.gas_price
            
            # Send transaction
            tx_hash = pc.web3.eth.send_transaction(tx)
            print(f"   Success! TX Hash: {pc.web3.to_hex(tx_hash)}")
            return pc.web3.to_hex(tx_hash)
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n❌ All methods failed")
    return None

if __name__ == "__main__":
    result = asyncio.run(test_transaction())
    if result:
        print(f"\n✅ Transaction successful: {result}")
    else:
        print("\n⚠️  Could not send transaction")
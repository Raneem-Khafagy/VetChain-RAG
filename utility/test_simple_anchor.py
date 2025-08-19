#!/usr/bin/env python3
"""
Simple test to verify PureChain anchoring works
"""

import json
import time
import hashlib
import asyncio
from purechainlib import PureChain

async def test():
    # Connect
    pc = PureChain("testnet")
    pc.connect("742d620beac984c44bea9c3c8533b1d819a386a72ebd9bc3dcb47ee03d0034aa")
    print(f"Connected: {pc.address}")
    
    # Create test data
    data = {"test": "data", "time": time.time()}
    data_hex = "0x" + json.dumps(data).encode().hex()
    
    # Send transaction
    tx_dict = {
        "to": "0x0000000000000000000000000000000000000001",
        "value": 0,
        "data": data_hex
    }
    
    print("Sending transaction...")
    result = await pc.send(to=tx_dict)
    
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    if result:
        tx_hash = result.get('transactionHash')
        print(f"TX Hash: {tx_hash}")
        if tx_hash:
            if hasattr(tx_hash, 'hex'):
                print(f"Final hash: 0x{tx_hash.hex()}")
            else:
                print(f"Final hash: {tx_hash}")

asyncio.run(test())
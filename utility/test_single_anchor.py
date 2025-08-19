#!/usr/bin/env python3
"""
Test anchoring a single record to PureChain
"""

import json
import time
import hashlib
from purechainlib import PureChain

# Configuration
NETWORK = "testnet"
PRIVATE_KEY = "742d620beac984c44bea9c3c8533b1d819a386a72ebd9bc3dcb47ee03d0034aa"

def test_single_anchor():
    """Test anchoring a single record."""
    
    # Connect to PureChain
    print("Connecting to PureChain...")
    pc = PureChain(NETWORK)
    pc.connect(PRIVATE_KEY)
    print(f"Connected: {pc.address}")
    
    # Try to check balance
    try:
        balance = pc.balance()
        print(f"Balance: {balance} PURE")
    except Exception as e:
        print(f"Balance check error: {e}")
    
    # Create test data
    test_record = {
        "id": "test_001",
        "pet_name": "Test Pet",
        "timestamp": time.time()
    }
    
    # Create anchor data
    data = {
        "record_id": test_record["id"],
        "content_hash": hashlib.sha256(json.dumps(test_record).encode()).hexdigest(),
        "timestamp": int(time.time())
    }
    
    print(f"\nAnchoring data: {json.dumps(data, indent=2)}")
    
    # Try different methods to send transaction
    print("\n1. Testing pc.send() method...")
    try:
        result = pc.send(
            to="0x0000000000000000000000000000000000000001",
            value=0,
            data="0x" + json.dumps(data).encode().hex()
        )
        print(f"   Success! Result: {result}")
        if hasattr(result, 'hash'):
            print(f"   TX Hash: {result.hash}")
        return result
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing pc.execute() method...")
    try:
        result = pc.execute(
            to="0x0000000000000000000000000000000000000001",
            value=0,
            data="0x" + json.dumps(data).encode().hex()
        )
        print(f"   Success! Result: {result}")
        return result
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Testing pc.transaction() method...")
    try:
        result = pc.transaction(
            to="0x0000000000000000000000000000000000000001",
            value=0,
            data="0x" + json.dumps(data).encode().hex()
        )
        print(f"   Success! Result: {result}")
        return result
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Testing pc.tx() method...")
    try:
        result = pc.tx(
            to="0x0000000000000000000000000000000000000001",
            value=0,
            data="0x" + json.dumps(data).encode().hex()
        )
        print(f"   Success! Result: {result}")
        return result
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n❌ All methods failed. PureChain might not be properly configured.")
    return None

if __name__ == "__main__":
    result = test_single_anchor()
    if result:
        print("\n✅ Successfully anchored to PureChain!")
    else:
        print("\n⚠️  Could not anchor to PureChain - will use mock hashes")
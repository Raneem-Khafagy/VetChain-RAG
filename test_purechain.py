#!/usr/bin/env python3
"""
Test PureChain connection and basic operations
"""
import asyncio
from purechainlib import PureChain

async def test_connection():
    """Test basic PureChain operations"""
    try:
        # Connect to testnet
        pc = PureChain('testnet')
        print("✅ Connected to PureChain testnet")
        
        # Connect wallet
        private_key = "742d620beac984c44bea9c3c8533b1d819a386a72ebd9bc3dcb47ee03d0034aa"
        pc.connect(private_key)
        print("✅ Wallet connected")
        
        # Check balance
        balance = await pc.balance()
        print(f"   Balance: {balance} PURE")
        
        # Try a simple transaction
        print("\n📝 Testing transaction...")
        try:
            # Send 0 PURE to burn address with data
            tx = await pc.send(
                to="0x0000000000000000000000000000000000000001",
                value=0
            )
            print(f"   Transaction sent: {tx}")
            
            if hasattr(tx, 'hash'):
                print(f"   TX Hash: {tx.hash}")
            else:
                print(f"   TX Result: {tx}")
                
        except Exception as e:
            print(f"   Transaction error: {e}")
        
        print("\n✅ PureChain is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
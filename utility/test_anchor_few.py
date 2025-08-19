#!/usr/bin/env python3
"""
Test anchoring just a few records
"""

import json
import asyncio
from pathlib import Path
from anchor_purechain_real import PureChainAnchorer

async def test_few():
    """Test with just 3 records."""
    # Load synthetic records
    synth_file = Path("RAG/data/synth.jsonl")
    records = []
    with open(synth_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 3 and line.strip():  # Just first 3 records
                records.append(json.loads(line))
    
    print(f"Testing with {len(records)} records\n")
    
    # Initialize anchorer
    anchorer = PureChainAnchorer()
    anchorer.initialize()
    
    # Process records
    for i, record in enumerate(records, 1):
        print(f"\n[{i}/{len(records)}]")
        updated = await anchorer.process_record(record)
        
        if updated.get("onChainTxHash"):
            print(f"✅ Success! TX: {updated['onChainTxHash']}")
        else:
            print("❌ Failed to anchor")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_few())
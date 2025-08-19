#!/usr/bin/env python3
"""
Clear chain data from synthetic records for testing real anchoring
"""

import json
from pathlib import Path

# Load records
synth_file = Path("RAG/data/synth.jsonl")
records = []
with open(synth_file, 'r') as f:
    for line in f:
        if line.strip():
            record = json.loads(line)
            # Clear chain data
            record["onChainTxHash"] = ""
            record["onChainCid"] = ""
            record["anchoredAt"] = None
            records.append(record)

# Save cleared records
output_file = Path("RAG/data/synth_cleared.jsonl")
with open(output_file, 'w') as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

print(f"✅ Cleared chain data from {len(records)} records")
print(f"   Saved to: {output_file}")
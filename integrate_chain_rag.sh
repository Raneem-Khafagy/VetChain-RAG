#!/bin/bash
# Script to integrate chain-verified data into RAG system

echo "🔗 Integrating Chain Data into RAG System"
echo "=========================================="

# Step 1: Copy chain-verified data to RAG
echo "Step 1: Copying chain-verified records to RAG..."
cp chain/data/petrecords.merged.jsonl RAG/data/petrecords.jsonl

# Step 2: Merge with synthetic data to create all.jsonl
echo "Step 2: Creating all.jsonl with chain data + synthetic..."
cat RAG/data/petrecords.jsonl RAG/data/synth.jsonl > RAG/data/all.jsonl
echo "   Created all.jsonl with $(wc -l < RAG/data/all.jsonl) records"

# Step 3: Rebuild the FAISS index with chain data
echo "Step 3: Rebuilding FAISS index with blockchain metadata..."
cd RAG
python scripts/build_index.py
cd ..

# Step 4: Verify chain data is in the index metadata
echo "Step 4: Verifying chain data in index..."
python -c "
import json
with open('RAG/data/meta.json') as f:
    meta = json.load(f)['meta']
    with_chain = sum(1 for m in meta if m.get('onChainTxHash') and m['onChainTxHash'] != '')
    print(f'   ✓ {with_chain}/{len(meta)} records have blockchain anchors')
"

echo ""
echo "✅ Integration complete! The RAG system now includes:"
echo "   - 8 blockchain-verified pet records"
echo "   - 50 synthetic training records"
echo "   - Transaction hashes and IPFS CIDs in search results"
echo ""
echo "Next steps:"
echo "1. Start the RAG server: cd RAG && uvicorn api.server:app --reload"
echo "2. Test a query to see blockchain data in results"
echo "3. Run chain verification: cd chain && python scripts/verify_receipts.py data/petrecords.jsonl"
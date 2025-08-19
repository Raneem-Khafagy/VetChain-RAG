# Utility Scripts

This directory contains utility and test scripts for the VetChain-RAG system.

## Anchoring Scripts

- `anchor_purechain_real.py` - Main script to anchor records to PureChain blockchain
- `anchor_synthetic_records.py` - Script for synthetic record anchoring
- `anchor_with_purechainlib.py` - Alternative anchoring using purechainlib
- `anchor_to_purechain.js` - JavaScript version of anchoring script

## Test Scripts

- `test_simple_anchor.py` - Simple test for PureChain anchoring
- `test_single_anchor.py` - Test anchoring a single record
- `test_anchor_few.py` - Test anchoring a few records
- `test_purechain_transact.py` - Test PureChain transaction methods

## Data Management

- `clear_chain_data.py` - Clear blockchain data from records
- `fix_synth.py` - Fix synthetic data structure

## Logs

- `purechain_anchor.log` - Log from PureChain anchoring process
- `anchor_output.log` - General anchoring output log

## Results

Successfully anchored 50 synthetic records to PureChain with real transaction hashes.
All records now have:
- Real PureChain transaction hashes (e.g., `0xe81ea423f3b2d0ad2869732c0c2eb754db9df711c00cabd7704bb207ba5eb7d0`)
- IPFS CIDs (mock for now)
- Timestamps of anchoring
- Zero gas cost (FREE on PureChain!)
#!/usr/bin/env python3
"""
Fix synth.jsonl by adding missing blockchain fields with empty/null values.
This ensures compatibility with the RAG indexing system.
"""
import json
import sys
from pathlib import Path

def fix_synthetic_records(input_file: str, output_file: str):
    """
    Add missing blockchain fields to synthetic records.
    """
    fixed_count = 0
    total_count = 0
    
    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line_num, line in enumerate(fin, 1):
            if not line.strip():
                continue
            
            try:
                record = json.loads(line)
                total_count += 1
                
                # Add missing blockchain fields if not present
                if 'onChainTxHash' not in record:
                    record['onChainTxHash'] = ""
                    fixed_count += 1
                
                if 'onChainCid' not in record:
                    record['onChainCid'] = ""
                
                if 'anchoredAt' not in record:
                    record['anchoredAt'] = None
                
                # Write the fixed record
                fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                sys.exit(1)
    
    print(f"✅ Fixed {fixed_count}/{total_count} records")
    print(f"   Added missing blockchain fields (onChainTxHash, onChainCid, anchoredAt)")
    print(f"   Output: {output_file}")
    
    return fixed_count, total_count

def verify_fix(file_path: str):
    """
    Verify all records have the required fields.
    """
    print(f"\nVerifying {file_path}...")
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            record = json.loads(line)
            
            # Check required fields exist
            assert 'onChainTxHash' in record, f"Line {line_num}: Missing onChainTxHash"
            assert 'onChainCid' in record, f"Line {line_num}: Missing onChainCid"
            assert 'anchoredAt' in record, f"Line {line_num}: Missing anchoredAt"
    
    print("✅ All records have required blockchain fields")

def main():
    # Define paths
    input_path = "RAG/data/synth.jsonl"
    output_path = "RAG/data/synth_fixed.jsonl"
    
    if not Path(input_path).exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)
    
    # Fix the synthetic records
    print(f"Fixing synthetic records in {input_path}...")
    fixed, total = fix_synthetic_records(input_path, output_path)
    
    # Verify the fix
    verify_fix(output_path)
    
    # Show next steps
    print("\n📝 Next steps:")
    print("1. Back up original: mv RAG/data/synth.jsonl RAG/data/synth.jsonl.bak")
    print("2. Replace with fixed: mv RAG/data/synth_fixed.jsonl RAG/data/synth.jsonl")
    print("3. Recreate all.jsonl: cat RAG/data/petrecords.jsonl RAG/data/synth.jsonl > RAG/data/all.jsonl")
    print("4. Rebuild index: cd RAG && python scripts/build_index.py")

if __name__ == "__main__":
    main()
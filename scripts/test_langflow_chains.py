#!/usr/bin/env python3
"""
Langflow Chain Tester and Validator

This script helps test and validate Langflow persona chains.
Use it to verify chains return proper JSON and match expected schema.
"""

import requests
import json
import sys
import uuid
from typing import Dict, Any, List

# Configuration
LANGFLOW_BASE_URL = "http://localhost:7860"
API_KEY = "sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs"

# Test segment samples
TEST_SEGMENTS = {
    "humorous": {
        "text": "So I was at the store buying oat milk, and the cashier goes 'that'll be $8' and I'm like WHAT?! For plant water?!",
        "topic": "Lifestyle",
        "tone": "Humorous"
    },
    "formal": {
        "text": "Today we examine the socioeconomic implications of alternative dairy products in contemporary consumer markets.",
        "topic": "Academic",
        "tone": "Formal"
    },
    "excited": {
        "text": "OMG you guys, the new iPhone just dropped and it's INSANE! The camera is literally next level!",
        "topic": "Technology",
        "tone": "Excited"
    },
    "controversial": {
        "text": "Let's talk politics - the latest scandal has everyone divided and honestly, things are getting pretty heated.",
        "topic": "Politics",
        "tone": "Serious"
    }
}


def test_langflow_chain(chain_name: str, segment: Dict[str, str], verbose: bool = True) -> Dict[str, Any]:
    """
    Test a Langflow chain with a segment.
    
    Args:
        chain_name: Name of the chain (e.g., 'genz_chain')
        segment: Segment dict with text, topic, tone
        verbose: Print detailed output
        
    Returns:
        Parsed response dict or error dict
    """
    url = f"{LANGFLOW_BASE_URL}/api/v1/run/{chain_name}"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    # Langflow expects the segment as a JSON string in input_value
    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": json.dumps(segment),
        "session_id": str(uuid.uuid4())
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Testing: {chain_name}")
        print(f"Segment: {segment['text'][:60]}...")
        print(f"{'='*60}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract the actual message from Langflow's nested response
        try:
            message_text = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
            
            # Try to parse as JSON
            result = json.loads(message_text)
            
            if verbose:
                print(f"✓ Response received")
                print(f"  Score: {result.get('score', 'N/A')}")
                print(f"  Opinion: {result.get('opinion', 'N/A')}")
                print(f"  Confidence: {result.get('confidence', 'N/A')}")
                print(f"  Note: {result.get('note', 'N/A')}")
            
            return result
            
        except (KeyError, json.JSONDecodeError) as e:
            if verbose:
                print(f"✗ Failed to parse response: {e}")
                print(f"  Raw response: {json.dumps(data, indent=2)}")
            return {"error": f"Parse error: {e}", "raw": data}
    
    except requests.exceptions.Timeout:
        if verbose:
            print(f"✗ Request timed out after 30 seconds")
        return {"error": "Timeout"}
    
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"✗ Request failed: {e}")
        return {"error": str(e)}


def validate_response(response: Dict[str, Any], chain_name: str) -> List[str]:
    """
    Validate that a response has required fields and correct types.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if "error" in response:
        errors.append(f"Response contains error: {response['error']}")
        return errors
    
    # Required fields
    required_fields = {
        "score": int,
        "opinion": str,
        "rationale": str,
        "confidence": float,
        "note": str
    }
    
    for field, field_type in required_fields.items():
        if field not in response:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(response[field], field_type):
            errors.append(f"Field '{field}' should be {field_type.__name__}, got {type(response[field]).__name__}")
    
    # Validate score range
    if "score" in response and isinstance(response["score"], int):
        if not 1 <= response["score"] <= 5:
            errors.append(f"Score {response['score']} out of range (must be 1-5)")
    
    # Validate confidence range
    if "confidence" in response and isinstance(response["confidence"], (int, float)):
        if not 0.0 <= response["confidence"] <= 1.0:
            errors.append(f"Confidence {response['confidence']} out of range (must be 0.0-1.0)")
    
    return errors


def test_all_chains():
    """Test all configured chains with various segments."""
    chains = ["genz_chain", "advertiser_chain"]
    
    print("\n" + "="*70)
    print(" LANGFLOW CHAIN VALIDATION TEST SUITE")
    print("="*70)
    
    results = {}
    
    for chain in chains:
        print(f"\n📋 Testing {chain.upper()}...")
        chain_results = {}
        
        for test_name, segment in TEST_SEGMENTS.items():
            response = test_langflow_chain(chain, segment, verbose=False)
            errors = validate_response(response, chain)
            
            chain_results[test_name] = {
                "response": response,
                "errors": errors,
                "valid": len(errors) == 0
            }
            
            # Quick summary
            if errors:
                print(f"  ✗ {test_name}: {len(errors)} errors")
                for error in errors:
                    print(f"    - {error}")
            else:
                score = response.get("score", "?")
                conf = response.get("confidence", "?")
                print(f"  ✓ {test_name}: score={score}, confidence={conf}")
        
        results[chain] = chain_results
    
    # Final summary
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70)
    
    for chain, chain_results in results.items():
        valid_count = sum(1 for r in chain_results.values() if r["valid"])
        total_count = len(chain_results)
        
        status = "✓ PASS" if valid_count == total_count else "✗ FAIL"
        print(f"{status} {chain}: {valid_count}/{total_count} tests passed")
    
    return results


def test_single_chain(chain_name: str, segment_type: str = "humorous"):
    """Quick test of a single chain with one segment."""
    if segment_type not in TEST_SEGMENTS:
        print(f"Error: Unknown segment type '{segment_type}'")
        print(f"Available: {', '.join(TEST_SEGMENTS.keys())}")
        return
    
    segment = TEST_SEGMENTS[segment_type]
    response = test_langflow_chain(chain_name, segment, verbose=True)
    errors = validate_response(response, chain_name)
    
    if errors:
        print(f"\n⚠️  Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✓ Response is valid!")
    
    return response


def check_langflow_health():
    """Check if Langflow is accessible."""
    try:
        response = requests.get(f"{LANGFLOW_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Langflow is running")
            return True
        else:
            print(f"✗ Langflow returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to Langflow: {e}")
        print(f"  Make sure Langflow is running on {LANGFLOW_BASE_URL}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Langflow persona chains")
    parser.add_argument(
        "command",
        choices=["health", "test", "validate"],
        help="Command to run"
    )
    parser.add_argument(
        "--chain",
        default="genz_chain",
        help="Chain name to test (default: genz_chain)"
    )
    parser.add_argument(
        "--segment",
        default="humorous",
        choices=list(TEST_SEGMENTS.keys()),
        help="Segment type to test (default: humorous)"
    )
    
    args = parser.parse_args()
    
    if args.command == "health":
        check_langflow_health()
    
    elif args.command == "test":
        if not check_langflow_health():
            sys.exit(1)
        test_single_chain(args.chain, args.segment)
    
    elif args.command == "validate":
        if not check_langflow_health():
            sys.exit(1)
        results = test_all_chains()
        
        # Exit with error if any tests failed
        all_valid = all(
            r["valid"] 
            for chain_results in results.values() 
            for r in chain_results.values()
        )
        sys.exit(0 if all_valid else 1)

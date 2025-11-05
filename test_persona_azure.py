#!/usr/bin/env python3
"""Test Azure OpenAI persona evaluation"""

import sys
sys.path.insert(0, '/home/runner/workspace')

from app.services.langflow_client import call_langflow_chain

test_segment = {
    "text": "This is a test segment about social media and viral content. It's super lit and totally relatable!",
    "topic": "Entertainment",
    "tone": "Excited"
}

print("Testing Azure OpenAI Persona Evaluation...")
print(f"Test segment: {test_segment}\n")

print("=" * 60)
print("Testing GenZ Chain")
print("=" * 60)
try:
    genz_result = call_langflow_chain("genz_chain", test_segment)
    print(f"✅ GenZ Evaluation Success!")
    print(f"   Score: {genz_result['score']}/5")
    print(f"   Opinion: {genz_result['opinion']}")
    print(f"   Rationale: {genz_result['rationale']}")
    print(f"   Confidence: {genz_result['confidence']}")
except Exception as e:
    print(f"❌ GenZ Evaluation Failed: {e}")

print("\n" + "=" * 60)
print("Testing Advertiser Chain")
print("=" * 60)
try:
    advertiser_result = call_langflow_chain("advertiser_chain", test_segment)
    print(f"✅ Advertiser Evaluation Success!")
    print(f"   Score: {advertiser_result['score']}/5")
    print(f"   Opinion: {advertiser_result['opinion']}")
    print(f"   Rationale: {advertiser_result['rationale']}")
    print(f"   Confidence: {advertiser_result['confidence']}")
except Exception as e:
    print(f"❌ Advertiser Evaluation Failed: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

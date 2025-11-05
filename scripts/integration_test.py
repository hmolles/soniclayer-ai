#!/usr/bin/env python3
"""
Integration Test Script for SonicLayer AI MVP

This script tests the complete pipeline:
1. Upload audio file
2. Wait for Langflow processing
3. Retrieve and display enriched segments with persona scores

Usage:
    python scripts/integration_test.py test1.wav
"""

import sys
import time
import requests
import json
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
LANGFLOW_URL = "http://localhost:7860"
LANGFLOW_API_KEY = "sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs"


def test_langflow_health():
    """Check if Langflow is accessible"""
    try:
        response = requests.get(f"{LANGFLOW_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Langflow is running")
            return True
        else:
            print(f"✗ Langflow health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot reach Langflow: {e}")
        return False


def test_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/segments/test", timeout=5)
        # We expect 404 for non-existent audio, which means the endpoint works
        if response.status_code in [404, 200]:
            print("✓ Backend is running")
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot reach backend: {e}")
        return False


def upload_audio(file_path):
    """Upload audio file to /evaluate/ endpoint"""
    print(f"\n📤 Uploading {file_path}...")
    
    if not Path(file_path).exists():
        print(f"✗ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "audio/wav")}
            response = requests.post(
                f"{API_BASE_URL}/evaluate/",
                files=files,
                timeout=180  # Increased for Whisper timestamp processing
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Upload successful!")
            print(f"  Audio ID: {data['audio_id']}")
            print(f"  Status: {data['status']}")
            print(f"  Segments: {data.get('segment_count', 'N/A')}")
            print(f"  Job IDs: {json.dumps(data.get('job_ids', {}), indent=4)}")
            return data
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None


def wait_for_processing(audio_id, timeout=240):
    """Wait for persona agents to process segments"""
    print(f"\n⏳ Waiting for Langflow processing (max {timeout}s)...")
    print("   This may take several minutes as each segment calls the LLM...")
    
    start_time = time.time()
    dots = 0
    last_genz_count = 0
    last_advertiser_count = 0
    
    while (time.time() - start_time) < timeout:
        try:
            # Check if persona feedback exists in segments
            response = requests.get(f"{API_BASE_URL}/segments/{audio_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                segments = data.get("segments", [])
                total_segments = len(segments)
                
                # Count how many segments have been processed by each persona
                genz_count = sum(1 for seg in segments if "genz" in seg)
                advertiser_count = sum(1 for seg in segments if "advertiser" in seg)
                
                # Show progress if changed
                if genz_count != last_genz_count or advertiser_count != last_advertiser_count:
                    print(f"   Progress: GenZ {genz_count}/{total_segments}, Advertiser {advertiser_count}/{total_segments}   ")
                    last_genz_count = genz_count
                    last_advertiser_count = advertiser_count
                
                # Check if ALL segments have BOTH persona scores
                if genz_count == total_segments and advertiser_count == total_segments:
                    elapsed = int(time.time() - start_time)
                    print(f"\n✓ Processing complete! ({elapsed}s)")
                    return True
            
            # Print waiting message
            if dots % 10 == 0:
                elapsed = int(time.time() - start_time)
                print(f"   Waiting... {elapsed}s (GenZ: {last_genz_count}, Advertiser: {last_advertiser_count})   ", end="\r")
            dots += 1
            time.sleep(3)
            
        except Exception as e:
            print(f"\n⚠ Error checking status: {e}")
            time.sleep(5)
    
    print(f"\n⚠ Timeout reached after {timeout}s")
    print(f"  Final status: GenZ {last_genz_count}/{total_segments}, Advertiser {last_advertiser_count}/{total_segments}")
    print("  Processing may still be ongoing. Check manually with:")
    print(f"  curl http://localhost:8000/segments/{audio_id} | jq")
    return False


def get_segments(audio_id):
    """Retrieve enriched segments with persona scores"""
    print(f"\n📊 Retrieving segments for {audio_id}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/segments/{audio_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            segments = data.get("segments", [])
            print(f"✓ Retrieved {len(segments)} segments")
            return segments
        else:
            print(f"✗ Failed to retrieve segments: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error retrieving segments: {e}")
        return None


def display_segment_summary(segments):
    """Display summary of segments with persona scores"""
    if not segments:
        print("No segments to display")
        return
    
    print(f"\n{'='*80}")
    print(f"SEGMENT ANALYSIS SUMMARY ({len(segments)} segments)")
    print(f"{'='*80}\n")
    
    for i, seg in enumerate(segments):
        print(f"Segment #{i} ({seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s)")
        print(f"Topic: {seg.get('topic', 'N/A')} | Tone: {seg.get('tone', 'N/A')}")
        print(f"Text: {seg.get('transcript', '')[:80]}...")
        
        # GenZ scores
        if "genz" in seg:
            genz = seg["genz"]
            print(f"  🔥 GenZ: {genz.get('score', 'N/A')}/5 - {genz.get('opinion', 'N/A')}")
        else:
            print(f"  🔥 GenZ: (not yet processed)")
        
        # Advertiser scores
        if "advertiser" in seg:
            adv = seg["advertiser"]
            print(f"  💼 Advertiser: {adv.get('score', 'N/A')}/5 - {adv.get('opinion', 'N/A')}")
        else:
            print(f"  💼 Advertiser: (not yet processed)")
        
        print()
    
    print(f"{'='*80}\n")


def main():
    """Main integration test flow"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/integration_test.py <audio_file.wav>")
        print("Example: python scripts/integration_test.py test1.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    print("="*80)
    print("SONICLAYER AI - INTEGRATION TEST")
    print("="*80)
    
    # Health checks
    print("\n🔍 Health Checks:")
    if not test_backend_health():
        print("\n❌ Backend is not running. Start with:")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)
    
    if not test_langflow_health():
        print("\n❌ Langflow is not running. Start with:")
        print("   docker-compose up -d")
        sys.exit(1)
    
    print("\n⚠️  Make sure RQ worker is running in a separate terminal:")
    print("   source venv/bin/activate && rq worker transcript_tasks")
    input("\nPress Enter when worker is running...")
    
    # Upload audio
    result = upload_audio(audio_file)
    if not result:
        sys.exit(1)
    
    audio_id = result.get("audio_id")
    status = result.get("status")
    
    # If already processed, just retrieve
    if status == "already_processed":
        print("\n📋 Audio already processed. Retrieving existing results...")
        segments = get_segments(audio_id)
        if segments:
            display_segment_summary(segments)
        sys.exit(0)
    
    # Wait for processing
    if wait_for_processing(audio_id, timeout=240):
        segments = get_segments(audio_id)
        if segments:
            display_segment_summary(segments)
            
            # Save to file
            output_file = f"test_results_{audio_id[:8]}.json"
            with open(output_file, "w") as f:
                json.dump({"audio_id": audio_id, "segments": segments}, f, indent=2)
            print(f"💾 Full results saved to: {output_file}")
    else:
        print("\n⚠ Processing incomplete. You can check later with:")
        print(f"   curl http://localhost:8000/segments/{audio_id} | jq")


if __name__ == "__main__":
    main()

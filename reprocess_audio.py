#!/usr/bin/env python3
"""
Re-process existing audio file and show detailed progress
"""
import time
import requests
import json
from pathlib import Path

API_BASE_URL = "http://localhost:8000"
AUDIO_FILE = "uploads/50f5315356317fa1a803bc5a754e4899d3275b711590f5baa7db35947f04bf70.wav"

print("="*80)
print("SONICLAYER AI - RE-PROCESSING AUDIO")
print("="*80)

# Re-upload the audio file
print(f"\n📤 Re-uploading audio file...")
print(f"   File: {AUDIO_FILE}")
print(f"   Size: {Path(AUDIO_FILE).stat().st_size / (1024*1024):.1f} MB")

with open(AUDIO_FILE, "rb") as f:
    files = {"file": (Path(AUDIO_FILE).name, f, "audio/wav")}
    response = requests.post(
        f"{API_BASE_URL}/evaluate/",
        files=files,
        timeout=300
    )

if response.status_code != 200:
    print(f"✗ Upload failed: {response.status_code}")
    print(f"  Response: {response.text}")
    exit(1)

data = response.json()
audio_id = data['audio_id']
print(f"\n✓ Upload successful!")
print(f"  Audio ID: {audio_id}")
print(f"  Status: {data['status']}")
print(f"  Segments: {data.get('segment_count', 'N/A')}")
print(f"  Transcript length: {data.get('transcript_length', 'N/A')} chars")
print(f"  Job IDs:")
print(f"    - GenZ: {data.get('job_ids', {}).get('genz', 'N/A')}")
print(f"    - Advertiser: {data.get('job_ids', {}).get('advertiser', 'N/A')}")

# Wait for persona processing
print(f"\n⏳ Waiting for persona agent processing...")
print("   This may take several minutes as each segment calls Azure GPT-4o-mini...")
print()

start_time = time.time()
last_genz_count = 0
last_advertiser_count = 0
total_segments = data.get('segment_count', 0)

while (time.time() - start_time) < 300:  # 5 minute timeout
    try:
        response = requests.get(f"{API_BASE_URL}/segments/{audio_id}", timeout=10)
        if response.status_code == 200:
            seg_data = response.json()
            segments = seg_data.get("segments", [])
            
            # Count processed segments
            genz_count = sum(1 for seg in segments if "genz" in seg)
            advertiser_count = sum(1 for seg in segments if "advertiser" in seg)
            
            # Show progress if changed
            if genz_count != last_genz_count or advertiser_count != last_advertiser_count:
                elapsed = int(time.time() - start_time)
                print(f"   [{elapsed:3d}s] Progress: GenZ {genz_count:2d}/{total_segments}, Advertiser {advertiser_count:2d}/{total_segments}")
                last_genz_count = genz_count
                last_advertiser_count = advertiser_count
            
            # Check if complete
            if genz_count == total_segments and advertiser_count == total_segments:
                elapsed = int(time.time() - start_time)
                print(f"\n✓ Processing complete! ({elapsed}s)")
                break
        
        time.sleep(3)
        
    except Exception as e:
        print(f"\n⚠ Error checking status: {e}")
        time.sleep(5)
else:
    print(f"\n⏱ Timeout reached after {int(time.time() - start_time)}s")

# Retrieve final segments
print(f"\n📊 Retrieving final segments...")
response = requests.get(f"{API_BASE_URL}/segments/{audio_id}", timeout=10)
if response.status_code == 200:
    seg_data = response.json()
    segments = seg_data.get("segments", [])
    print(f"✓ Retrieved {len(segments)} segments\n")
    
    print(f"{'='*80}")
    print(f"SEGMENT ANALYSIS SUMMARY ({len(segments)} segments)")
    print(f"{'='*80}\n")
    
    for i, seg in enumerate(segments):
        print(f"Segment #{i} ({seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s)")
        print(f"Topic: {seg.get('topic', 'N/A')} | Tone: {seg.get('tone', 'N/A')}")
        print(f"Text: {seg.get('transcript', '')[:100]}...")
        
        # GenZ scores
        if "genz" in seg:
            genz = seg["genz"]
            print(f"  🔥 GenZ: {genz.get('score', 'N/A')}/5 - {genz.get('opinion', 'N/A')[:80]}")
            if genz.get('reasoning'):
                print(f"      Reasoning: {genz.get('reasoning', '')[:80]}...")
        else:
            print(f"  🔥 GenZ: (not yet processed)")
        
        # Advertiser scores
        if "advertiser" in seg:
            adv = seg["advertiser"]
            print(f"  💼 Advertiser: {adv.get('score', 'N/A')}/5 - {adv.get('opinion', 'N/A')[:80]}")
            if adv.get('reasoning'):
                print(f"      Reasoning: {adv.get('reasoning', '')[:80]}...")
        else:
            print(f"  💼 Advertiser: (not yet processed)")
        
        print()
    
    print(f"{'='*80}\n")
    print("✓ Dashboard should now be interactive with all segments!")
    print(f"  View at: http://localhost:5000")
else:
    print(f"✗ Failed to retrieve segments: {response.status_code}")

# Langflow Setup - Next Steps

## ✅ Current Status
- Langflow is running and accessible at http://localhost:7860
- Chains created in Langflow UI
- LLM model is still downloading in LM Studio

---

## ⏳ Waiting for LM Studio Model

Once your model finishes downloading in LM Studio:

1. **Load the model** in LM Studio
2. **Note the model name** (shown in LM Studio interface)
3. **Update your Langflow chains**:
   - Go to each flow (genz_chain, advertiser_chain)
   - Click the **OpenAI component**
   - Set **Model Name** to the exact name from LM Studio
   - Click **Save**

---

## 🔍 Verify Endpoint Names Are Set

The test script couldn't find your chains, which means the endpoint names might not be configured yet.

### How to Set Endpoint Names:

For **each flow** (genz_chain and advertiser_chain):

1. Open the flow in Langflow
2. Click the **"Share"** button (top right corner)
3. In the popup, look for **"Endpoint Name"** or **"Tweaks"** section
4. Set the endpoint name:
   - For GenZ flow: `genz_chain`
   - For Advertiser flow: `advertiser_chain`
5. Click **Save** or **Apply**
6. **Save the flow** (floppy disk icon)

### Alternative Method (if above doesn't work):

1. Open each flow
2. Look for flow **Settings** or **Configuration** (gear icon)
3. Find **"API Endpoint"** or **"Flow Name"** field
4. Make sure it matches: `genz_chain` or `advertiser_chain`

---

## 🧪 Manual Testing (Once Model is Loaded)

### Test GenZ Chain:
```bash
curl -X POST http://localhost:7860/api/v1/run/genz_chain \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs" \
  -d '{
    "input_value": "This podcast is super cool! We are talking about the latest tech trends.",
    "output_type": "chat",
    "input_type": "chat"
  }' | jq
```

### Test Advertiser Chain:
```bash
curl -X POST http://localhost:7860/api/v1/run/advertiser_chain \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs" \
  -d '{
    "input_value": "Professional discussion about business technology solutions.",
    "output_type": "chat",
    "input_type": "chat"
  }' | jq
```

**Expected response:**
```json
{
  "outputs": [
    {
      "outputs": [
        {
          "results": {
            "message": {
              "text": "{\"score\": 4, \"opinion\": \"...\", ...}"
            }
          }
        }
      ]
    }
  ]
}
```

---

## 🚀 Using the Test Script

Once model is loaded and endpoints are configured, run:

### Check Langflow Health:
```bash
python scripts/test_langflow_chains.py health
```

### Test Single Chain:
```bash
python scripts/test_langflow_chains.py test --chain genz_chain --segment humorous
```

### Validate All Chains:
```bash
python scripts/test_langflow_chains.py validate
```

**Note:** Don't copy from hyperlinks - type the command directly or copy from here!

---

## 🐛 Troubleshooting

### "bash: syntax error near unexpected token"
**Problem:** You copied `python [test_langflow_chains.py](http://...)` from a hyperlink  
**Solution:** Use `python scripts/test_langflow_chains.py validate` instead

### Chains return HTML instead of JSON
**Problem:** Endpoint names not set correctly in Langflow  
**Solution:** Follow "Verify Endpoint Names Are Set" section above

### "Model not found" or connection errors
**Problem:** LM Studio model not loaded or wrong model name  
**Solution:** 
1. Wait for model download to complete
2. Load model in LM Studio
3. Update model name in Langflow OpenAI component
4. Restart the flow

### Empty or invalid JSON response
**Problem:** Model not generating proper JSON  
**Solution:**
1. Test the flow in Langflow's Playground first
2. Make sure prompt is pasted correctly
3. Try lowering temperature to 0.5 for more consistent output
4. Increase Max Tokens to 500 or 1000

---

## 📋 Quick Checklist

Before running the test script:

- [ ] LM Studio model finished downloading
- [ ] Model is loaded in LM Studio (green "Running" status)
- [ ] Model name noted from LM Studio
- [ ] Both flows created in Langflow (genz_chain, advertiser_chain)
- [ ] OpenAI component in both flows has correct Model Name
- [ ] Endpoint names set in both flows (Share → Endpoint Name)
- [ ] Both flows saved
- [ ] Tested one flow in Langflow Playground
- [ ] curl test returns JSON (not HTML)

Once all checked, run:
```bash
python scripts/test_langflow_chains.py validate
```

---

## 📞 Next Actions

1. **Wait for model download** - can take 5-60 minutes depending on model size
2. **Load model in LM Studio**
3. **Update model names** in Langflow OpenAI components
4. **Set endpoint names** properly (see section above)
5. **Test manually** with curl commands
6. **Run validation script** once manual tests work

After validation passes, you're ready for integration testing with the full backend!

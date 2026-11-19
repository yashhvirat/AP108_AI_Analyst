import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/chat"
# MODEL = "llama3.2" 
MODEL = "qwen3.5:4b"


def generate_dax(question, schema_context):
    
    prompt = f"""
You are a Power BI DAX query generator.

USER QUESTION:
{question}

POWER BI MODEL SCHEMA:
{schema_context}

YOUR TASK:
Generate one executable DAX query answering the user's question.

STRICT RULES:
1. Use only measures, tables and columns present in the schema.
2. Prefer an existing measure when it directly answers the question.
3. Never use a subset measure to answer a total measure question.
4. For "total cases", do not use abandoned, IFT abandoned,
   neonatal abandoned, or other subset measures.
5. If no suitable existing measure or valid column is available,
   return needs_clarification. Never invent names.
6. DAX must be an executable query starting with EVALUATE.
7. For a single KPI, use ROW().
8. Do not generate measure definitions or calculated columns.
9. Return ONLY the required JSON object.

OUTPUT FORMAT:
{{
  "status": "success",
  "dax": "EVALUATE ROW(...)",
  "explanation": "Brief explanation"
}}

If clarification is required:
{{
  "status": "needs_clarification",
  "dax": "",
  "explanation": "Explain what is missing"
}}
"""

    response_format = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["success", "needs_clarification"]
            },
            "dax": {"type": "string"},
            "explanation": {"type": "string"}
        },
        "required": ["status", "dax", "explanation"],
        "additionalProperties": False
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": response_format,
        "think": False,
        "options": {
            "temperature": 0,
            "num_ctx": 8192,
            "num_predict": 512
        }
    }

    start_time = time.time()

    try:
        print("Sending Post Request")
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=600
        )

        print("Received Response")
        
        
        response.raise_for_status()

        raw_response = response.json()

        print("\n========== OLLAMA RAW RESPONSE ==========")
        print(raw_response)
        print("=========================================\n")

        content = raw_response.get("message", {}).get("content", "")

        if not content or not content.strip():
            raise ValueError(
                "Ollama returned empty content. "
                f"Response details: {raw_response}"
            )

        result = json.loads(content)

        required_keys = {"status", "dax", "explanation"}

        if set(result.keys()) != required_keys:
            raise ValueError(
                f"Invalid Ollama response structure: {result}"
            )

        if result["status"] == "success":
            if not result["dax"].strip().upper().startswith("EVALUATE"):
                raise ValueError("AI did not generate an executable DAX query")

        return result


    except requests.exceptions.ReadTimeout:
        raise TimeoutError(
            "Ollama took more than 10 minutes. "
            "Try a smaller model schema or a faster local model."
        )

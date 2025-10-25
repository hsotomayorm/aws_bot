# app.py (con lectura explícita de credenciales desde ENV)
import os
from flask import Flask, request, jsonify
import boto3
from botocore.config import Config

REGION     = os.getenv("AWS_REGION")
KB_ID      = os.getenv("KB_ID")
MODEL_ARN  = os.getenv("MODEL_ARN", "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0")

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# ========= OPCIÓN B: CREDENCIALES TEMPORALES (STS) =========
# Si estás asumiendo un rol / SSO y te entregan token, rellena también:
AWS_SESSION_TOKEN = None  # Ej: "IQoJb3JpZ2luX2VjEBoa..."  (o deja None si no aplica)

# Si hay variables, crea sesión con ellas; si no, usa el proveedor por defecto (perfil/rol)
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION,
    )
else:
    # Perfil/rol (lo más seguro en prod)
    session = boto3.Session(region_name=REGION)

client = session.client(
    "bedrock-agent-runtime",
    config=Config(retries={"max_attempts": 10, "mode": "standard"})
)

app = Flask(__name__)

@app.post("/ask")
def ask():
    data = request.get_json(force=True) or {}
    question = data.get("question", "").strip()
    kb_id = data.get("kbId") or KB_ID
    model_arn = data.get("modelArn") or MODEL_ARN
    gen_cfg = data.get("generation")  # opcional: {"temperature":0.2, "maxTokens":400}

    if not question:
        return jsonify(error="missing question"), 400
    if not kb_id:
        return jsonify(error="missing KB_ID (env KB_ID or body.kbId)"), 400

    params = {
        "input": {"text": question},
        "retrieveAndGenerateConfiguration": {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn
            }
        }
    }
    if gen_cfg:
        params["generationConfiguration"] = gen_cfg

    resp = client.retrieve_and_generate(**params)
    answer = resp["output"]["text"]
    sources = []
    for att in resp.get("citations", []):
        for ref in att.get("retrievedReferences", []):
            loc = ref.get("location", {}) or {}
            uri = loc.get("s3Location") or loc.get("webLocation") or loc
            sources.append({"uri": uri, "score": ref.get("score")})

    return jsonify({"answer": answer, "sources": sources})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

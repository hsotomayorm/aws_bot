import os
from flask import Flask, request, jsonify
import boto3
from botocore.config import Config

REGION     = os.getenv("AWS_REGION", os.getenv("REGION", "us-west-2"))
KB_ID      = os.getenv("KB_ID", "")
MODEL_ARN  = os.getenv("MODEL_ARN", "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0")

# Para Code Engine, recomienda usar variables de entorno/Secrets.
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN     = os.getenv("AWS_SESSION_TOKEN")  # opcional

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION,
    )
else:
    # Si no hay claves, boto3 intentará resolver con variables/IMDS (no aplica en CE), por eso se sugiere setearlas como Secrets.
    session = boto3.Session(region_name=REGION)

client = session.client(
    "bedrock-agent-runtime",
    config=Config(retries={"max_attempts": 10, "mode": "standard"})
)

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(ok=True), 200

@app.post("/ask")
def ask():
    data = request.get_json(force=True) or {}
    question = (data.get("question") or "").strip()
    kb_id = data.get("kbId") or KB_ID
    model_arn = data.get("modelArn") or MODEL_ARN
    gen_cfg = data.get("generation")  # opcional

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
    answer = resp.get("output", {}).get("text", "")
    sources = []
    for att in resp.get("citations", []):
        for ref in att.get("retrievedReferences", []):
            loc = ref.get("location", {}) or {}
            uri = loc.get("s3Location") or loc.get("webLocation") or loc
            sources.append({"uri": uri, "score": ref.get("score")})

    return jsonify({"answer": answer, "sources": sources})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

import os
from flask import Flask, request, jsonify
import boto3
from botocore.config import Config

REGION     = os.getenv("AWS_REGION", os.getenv("REGION", "us-west-2"))
KB_ID      = os.getenv("KB_ID", "")
MODEL_ARN  = os.getenv("MODEL_ARN", "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0")

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN     = os.getenv("AWS_SESSION_TOKEN") or None  # 👈 aquí está la clave

# boto3 solo necesita el token si existe realmente
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,  # será None si no existe
        region_name=REGION,
    )
else:
    session = boto3.Session(region_name=REGION)

client = session.client(
    "bedrock-agent-runtime",
    config=Config(retries={"max_attempts": 10, "mode": "standard"})
)

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify(ok=True)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify(error="missing question"), 400

    params = {
        "input": {"text": question},
        "retrieveAndGenerateConfiguration": {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": MODEL_ARN
            }
        }
    }

    resp = client.retrieve_and_generate(**params)
    return jsonify(resp)

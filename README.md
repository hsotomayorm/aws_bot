# Flask + AWS Bedrock (Knowledge Base) en IBM Cloud Code Engine

Este proyecto empaqueta una API Flask que llama a **AWS Bedrock Agent Runtime** (`retrieve_and_generate`) con un **Knowledge Base**, lista para desplegar en **IBM Cloud Code Engine**.

## Variables de entorno requeridas
- `AWS_REGION` (o `REGION`) — ej: `us-west-2`
- `KB_ID` — tu `KnowledgeBaseId`
- `MODEL_ARN` — ej: `arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Credenciales AWS**: en Code Engine usa **Secrets** y/o **env vars**:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_SESSION_TOKEN` (si usas credenciales temporales)

Endpoints:
- `GET /health`
- `POST /ask` → body: `{"question":"...", "kbId":"(opcional)", "modelArn":"(opcional)", "generation":{"temperature":0.2}}`

---

## Build & Push de imagen (IBM Cloud Container Registry)
```bash
ibmcloud login -r us-south
ibmcloud plugin install code-engine
ibmcloud plugin install container-registry

ibmcloud cr region-set us-south
ibmcloud cr namespace-add mi-namespace
ibmcloud cr login

export REGION=us-south
export NS=mi-namespace
export IMG=aws-bedrock-ce:latest

docker build -t $REGION.icr.io/$NS/$IMG .
docker push $REGION.icr.io/$NS/$IMG
```

## Despliegue en Code Engine
```bash
ibmcloud ce project create --name mi-proyecto || true
ibmcloud ce project select --name mi-proyecto

# (Opcional) crea un Secret para tus credenciales AWS
ibmcloud ce secret create --name aws-creds       --from-literal AWS_ACCESS_KEY_ID=AKIA...       --from-literal AWS_SECRET_ACCESS_KEY=xxxxxxxx       --from-literal AWS_SESSION_TOKEN=yyyyyyyy  # si aplica

ibmcloud ce app create       --name bedrock-app       --image $REGION.icr.io/$NS/$IMG       --port 8080       --cpu 0.25       --memory 0.5G       --min-scale 0       --max-scale 3       --env AWS_REGION=us-west-2       --env KB_ID=JOJNFCRK55       --env MODEL_ARN=arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0       --secret aws-creds
```

**Notas:**
- Code Engine tiene salida a Internet, por lo que puede invocar servicios AWS públicos.
- Si tu KB o fuentes requieren VPC privada en AWS, necesitarás exponerlos públicamente o un túnel seguro (no soportado nativamente por CE).
- Administra las rotaciones de keys desde AWS (STS/SO) y actualiza el Secret en CE cuando cambien.

## Logs y actualización
```bash
ibmcloud ce app logs --name bedrock-app --follow
docker build -t $REGION.icr.io/$NS/$IMG . && docker push $REGION.icr.io/$NS/$IMG
ibmcloud ce app update --name bedrock-app --image $REGION.icr.io/$NS/$IMG
```

## Desarrollo local
```bash
pip install -r requirements.txt
export AWS_REGION=us-west-2
export KB_ID=JOJNFCRK55
export MODEL_ARN=arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
# export AWS_ACCESS_KEY_ID=...
# export AWS_SECRET_ACCESS_KEY=...
# export AWS_SESSION_TOKEN=...   # si aplica

gunicorn wsgi:app -c gunicorn.conf.py
# http://localhost:8080/health
```

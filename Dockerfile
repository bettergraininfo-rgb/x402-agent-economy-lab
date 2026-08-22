# DIR-032 / PLAN-render-deploy-cutover Step 0 — persistent hosting for the
# x402 v2 exact-scheme rail (sui_market_server :8604 catalog).
# Public pay-to address is injected via the SELLER_ADDRESS env var (render.yaml);
# NO key material ships in this image — keyless hosts serve challenges fine.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY sui_market_server.py sui_x402_v2.py ./

ENV SELLER_ADDRESS=""
EXPOSE 10000

# Render injects $PORT; bind 0.0.0.0 as required by their routing layer.
CMD ["sh", "-c", "uvicorn sui_market_server:app --host 0.0.0.0 --port ${PORT:-10000}"]

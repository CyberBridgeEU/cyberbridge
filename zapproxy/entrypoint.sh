#!/bin/sh

# Clean stale ZAP session data on startup
echo "[entrypoint] Cleaning old ZAP session data..."
rm -rf /root/.ZAP/session/* /root/.ZAP/transfer/* /root/.ZAP/db/* 2>/dev/null
mkdir -p /root/.ZAP/session /root/.ZAP/transfer /root/.ZAP/db

# Background loop: purge ZAP session/transfer/db files every 6 hours
(
  while true; do
    sleep 21600  # 6 hours
    echo "[cleanup] Purging ZAP transient data..."
    rm -rf /root/.ZAP/session/* /root/.ZAP/transfer/* /root/.ZAP/db/* 2>/dev/null
  done
) &

# Start ZAP daemon and FastAPI
cd /zap/ZAP_2.16.1 && ./zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true &
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

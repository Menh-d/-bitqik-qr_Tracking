#!/bin/bash
# Script to launch Bitqik QR Studio Tracker WebApp

cd "$(dirname "$0")"
echo "=========================================================="
echo "🚀 ກຳລັງເລີ່ມລະບົບ Bitqik QR Studio Tracker..."
echo "=========================================================="

# Check if port 8000 is already in use
PORT=${1:-8000}

echo "👉 ເປີດ Browser ໄປທີ່: http://localhost:$PORT"
echo "📱 ສຳລັບມືຖືໃນ Wi-Fi ດຽວກັນ, ເບິ່ງ IP ທີ່ສະແດງດ້ານລຸ່ມ:"
echo ""

python3 server.py $PORT

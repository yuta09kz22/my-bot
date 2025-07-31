import os
import ccxt
import time
import logging
import sys
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pathlib import Path

# ✅ ロガー設定（stdout に出すよう明示）
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # stdout に出力
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

exchange = None
is_ready = False

def create_app():
    global exchange, is_ready

    app = Flask(__name__)

    try:
        # ✅ .envのパスを明示指定
        env_path = Path(__file__).resolve().parent / ".env"
        load_dotenv(dotenv_path=env_path)
        logger.info("✅ .env 読み込み完了")

        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("環境変数 BYBIT_API_KEY または BYBIT_API_SECRET が未設定です")

        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'linear',
                'adjustForTimeDifference': True,
                'recvWindow': 10000
            }
        })

        time.sleep(3)
        is_ready = True
        logger.info("✅ サーバー受信準備完了")

    except Exception as e:
        logger.error(f"❌ 初期化エラー: {e}")

    @app.route('/webhook', methods=['POST'])
    def webhook():
        if not is_ready:
            logger.warning("⚠️ サーバー準備未完了（is_ready=False）")
            return jsonify({"error": "Server not ready"}), 503

        data = request.json
        logger.info(f"📩 Webhook受信: {data}")
        return jsonify({"status": "OK"})

    return app

def get_app():
    return create_app()

app = get_app()

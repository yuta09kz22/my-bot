import ccxt
import os
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from threading import Event

load_dotenv()

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

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

app = Flask(__name__)
ready_event = Event()

def wait_until_ready():
    print("⏳ サーバー初期化中... 5秒待機")
    time.sleep(5)
    ready_event.set()
    print("✅ サーバー受信準備完了")

def get_current_position(symbol):
    positions = exchange.fetch_positions([symbol])
    for p in positions:
        if p['symbol'] == symbol and abs(p['contracts']) > 0:
            return {
                'side': 'long' if p['side'].lower() == 'long' else 'short',
                'contracts': p['contracts']
            }
    return None

def close_position(symbol, current_side):
    try:
        side = 'sell' if current_side == 'long' else 'buy'
        amount = exchange.fetch_position(symbol)['contracts']
        if amount == 0:
            return

        print(f"🚪 ポジション決済: {current_side.upper()} {amount}")
        exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=abs(amount),
            params={"reduceOnly": True}
        )
    except Exception as e:
        print(f"❌ 決済失敗: {e}")

def place_order(symbol, side):
    leverage = 10
    try:
        exchange.load_markets()

        try:
            exchange.set_leverage(leverage, symbol)
            print(f"✅ レバレッジを {leverage}x に設定しました: {symbol}")
        except ccxt.ExchangeError as e:
            if 'leverage not modified' in str(e).lower():
                print(f"ℹ️ レバレッジは既に設定済みです: {symbol}")
            else:
                raise e

        # 現在のポジション確認と決済処理
        current_position = get_current_position(symbol)
        if current_position:
            current_side = current_position['side']
            if (side.lower() == 'buy' and current_side == 'short') or (side.lower() == 'sell' and current_side == 'long'):
                close_position(symbol, current_side)
                print("⏳ 決済完了まで3秒待機")
                time.sleep(3)

        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0)
        print(f"💰 USDT残高: {usdt_balance}")

        price = exchange.fetch_ticker(symbol)['last']
        market = exchange.market(symbol)

        order_value = usdt_balance * 0.05 * leverage
        quantity_float = order_value / price
        quantity_str = exchange.amount_to_precision(symbol, quantity_float)
        quantity = float(quantity_str)
        min_amount = float(market['limits']['amount']['min'])

        if quantity < min_amount:
            return {'error': f"注文数量({quantity})が最小数量({min_amount})未満です"}

        if side.lower() == 'buy':
            tp_price_raw = price * 1.03
            sl_price_raw = price * 0.995
        else:
            tp_price_raw = price * 0.97
            sl_price_raw = price * 1.005

        tp_price = float(exchange.price_to_precision(symbol, tp_price_raw))
        sl_price = float(exchange.price_to_precision(symbol, sl_price_raw))

        min_price = market.get('limits', {}).get('price', {}).get('min', 0.00001)
        if tp_price < min_price or sl_price < min_price:
            return {'error': f"TP({tp_price})またはSL({sl_price})がBybitの最小価格({min_price})未満です"}

        params = {
            'takeProfit': str(tp_price),
            'stopLoss': str(sl_price)
        }

        print(f"🛒 注文実行: Side={side}, Qty={quantity}, TP={tp_price}, SL={sl_price}")
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=side.lower(),
            amount=quantity,
            price=None,
            params=params
        )

        return order

    except Exception as e:
        print(f"❌ 注文処理中のエラー: {e}")
        return {'error': str(e)}

@app.route('/webhook', methods=['POST'])
def webhook():
    if not ready_event.is_set():
        return jsonify({"error": "Server not ready"}), 503

    data = request.json
    print(f"📩 Received: {data}")

    symbol = data.get("symbol")
    side = data.get("side")

    if symbol and side:
        result = place_order(symbol, side)
        print(f"📦 Order Result: {result}")
        return jsonify({"result": result})
    else:
        return jsonify({"error": "symbol or side missing"}), 400

if __name__ == '__main__':
    import threading
    threading.Thread(target=wait_until_ready).start()
    app.run(port=5000)

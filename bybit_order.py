import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'linear',  # USDT建て無期限先物
        'adjustForTimeDifference': True,
    }
})


def place_order(symbol, side):
    # TradingViewからのsymbol整形（例: XRP/USDT:USDT → XRP/USDT）
    if ":USDT" in symbol:
        symbol = symbol.replace(":USDT", "")

    leverage = 20  # 任意のレバレッジ
    try:
        exchange.load_markets()
        market = exchange.market(symbol)

        # 残高取得＆注文数量計算
        balance = exchange.fetch_balance()
        usdt_balance = balance['total']['USDT']
        order_size = usdt_balance * 0.05

        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        quantity = round(order_size / price, 3)

        # 利確・損切りライン
        tp_price = round(price * 1.03, 4)  # 利確：3%
        sl_price = round(price * 0.98, 4)  # 損切り：2%

        # 注文パラメータ
        params = {
            'takeProfit': tp_price,
            'stopLoss': sl_price,
            'reduce_only': False,
            'leverage': leverage  # ← ここでレバレッジ指定！
        }

        # 指値注文（limit order）
        order = exchange.create_order(
         symbol=symbol,
         type="market",
         side=side.lower(),
         amount=quantity,
         price=None,  # market注文なので不要
         params={
          'takeProfit': tp_price,
          'stopLoss': sl_price,
          'leverage': leverage,
         }
        )
return order

    except Exception as e:
        return str(e)

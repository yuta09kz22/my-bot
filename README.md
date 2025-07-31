bybit_order.pyはテスト用です。

必要な物（ローカル実行に限る）
・ngrok ←webhookにポート制限があるため中継役
・trading view Essential以上のプラン ← webhookを使用するには必要
・pinescript　←注文発生トリガー　戦略に応じて必要なscriptを用意
・bybit API ←.envを同じ階層に配置してAPIキーとシークレットを記載(APIキー取得方法は別途調べる)

開発環境
・python3 flask dotenv ccxt

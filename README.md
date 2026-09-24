# サーマルセンサー

USB接続したMelexis EVB90640/41とMLX90641を読み、PC・スマホのブラウザへ温度分布を配信します。16×12画素のヒートマップと最高・最低・平均・周囲温度を表示します。

## 起動

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python thermal_web.py --host <サーバーのLAN側IP> --port 8765
```

実行ユーザーには `/dev/ttyACM0` へのアクセス権限が必要です。付属の `thermal-sensor.service.example` は `dialout` グループを付ける例です。USBのデバイス名が変わっても `--device auto` でMelexis評価ボードを探します。

同じLANのPC・スマホで `http://<サーバーのLAN側IP>:8765/` を開きます。温度データはサーバー内で取得し、ブラウザへJSONで渡します。公開範囲はLAN内に限定してください。外出先からのアクセスには、認証済みのVPNなど別の経路が必要です。

## サービス運用

`thermal-sensor.service.example` のユーザー・パス・`--host` を設置先に合わせて変更し、`/etc/systemd/system/thermal-sensor.service` に配置します。`sudo systemctl daemon-reload && sudo systemctl enable --now thermal-sensor` で常駐させます。ファイアウォールでは利用するLANのサブネットから、指定したLAN側IPの8765/tcpだけを許可します。

状態確認: `systemctl status thermal-sensor` / `curl http://<サーバーのLAN側IP>:8765/api/frame`

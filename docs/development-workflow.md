# 開発運用

## 方針

作業ブランチで変更し、PRとCIで検証してからdefault branchへ取り込みます。実機のサーバー設定は公開リポジトリに保存しません。

## 導入状況

最終確認日: 2026-09-24

| 項目 | 状態 | 根拠・補足 |
| --- | --- | --- |
| 指示 | 設定済み | `AGENTS.md` |
| CI | 設定済み | `.github/workflows/check.yml`。初回PRで実行結果を確認する |
| Issue / PR templates | 設定済み | `.github/ISSUE_TEMPLATE/`、`.github/pull_request_template.md` |
| branch保護 | 未確認 | 初回CI成功後にGitHub APIで確認・設定する |
| Project | 設定済み | [Development HQ](https://github.com/users/SHOHE001/projects/1) を再利用 |

## ローカル検証

`python3 -m py_compile thermal_web.py`、`node --check static/app.js`。実機では `/api/frame` の `status=live` と192画素を確認します。

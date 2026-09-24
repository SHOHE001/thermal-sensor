# 開発運用

## 方針

作業ブランチで変更し、PRとCIで検証してからdefault branchへ取り込みます。実機のサーバー設定は公開リポジトリに保存しません。

## 導入状況

最終確認日: 2026-09-25

| 項目 | 状態 | 根拠・補足 |
| --- | --- | --- |
| 指示 | 設定済み | `AGENTS.md` |
| CI | 設定済み | `.github/workflows/check.yml` の `syntax`。初回PRで成功を確認 |
| Issue / PR templates | 設定済み | `.github/ISSUE_TEMPLATE/`、`.github/pull_request_template.md` |
| branch保護 | 設定済み | `main` にPR・`syntax` 成功必須、adminにも適用、force push・削除を禁止。2026-09-25にGitHub APIでreadback |
| Project | 設定済み | [Development HQ](https://github.com/users/SHOHE001/projects/1) を再利用 |

## ローカル検証

`python3 -m py_compile thermal_web.py`、`node --check static/app.js`。実機では `/api/frame` の `status=live` と192画素を確認します。

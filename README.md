---
title: Duelデッキ勝率ボード
client: internal（個人プロジェクト）
type: plan
status: draft
confidentiality: public
created: 2026-11-13
updated: 2026-11-13
tags: [clash-royale, duel, crown-series, github-pages, github-actions]
---

# Duelデッキ勝率ボード

クラロワの対戦履歴から、Duel（Crown Series）のデッキ別勝率・pick順（何戦目に出したか）別の勝率を集計し、ボタン1つでアプリにデッキをコピーできるページ。

- 取得: GitHub Actions が30分ごとに公式API（RoyaleAPIプロキシ経由）から対戦履歴を取得し `data/` に蓄積
- 表示: GitHub Pages で `index.html` を公開（スマホのホーム画面に追加して使う）
- ストック: Duel用の4デッキセットを端末のブラウザに保存

## 必要な設定

- リポジトリの Secrets に `CR_API_KEY`（developer.clashroyale.com で IP `45.79.218.79` を許可して発行したキー）
- 任意: Variables に `CR_PLAYER_TAG`（既定 `#2J8GG89GY`）

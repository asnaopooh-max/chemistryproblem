# 化学基礎 共通テスト対策アプリ

このアプリは、化学基礎の共通テスト対策向けにランダム出題する完全静的な Web アプリです。ブラウザだけで動作し、サーバー通信や保存は行いません。

## 概要

- 5〜8択の単一選択問題を出題
- 分野を指定してランダム出題
- 解答送信後に正誤判定と解説を表示
- セッション内の解答数・正答数・正答率を表示
- localStorage / sessionStorage / Cookie を使用しない

## フォルダ構成

```
chem-basic-quiz-app/
├─ index.html
├─ README.md
├─ css/
│  └─ style.css
├─ js/
│  ├─ app.js
│  ├─ quizEngine.js
│  ├─ questionLoader.js
│  └─ constants.js
├─ data/
│  ├─ questions.json
│  └─ schema.md
└─ docs/
   ├─ question-authoring-guide.md
   └─ future-extension-plan.md
```

## 起動方法

1. ブラウザで直接開く場合、`index.html` を開いて動作することを確認してください。
2. `fetch` で `questions.json` を読み込むため、ローカルサーバーを使うことをおすすめします。

```bash
python -m http.server 8000
```

その後、ブラウザで次の URL を開きます。

```
http://localhost:8000
```

## 問題の追加方法

1. `data/questions.json` に新しい問題を追加します。
2. `id` を重複しないように設定します。
3. `category` は `js/constants.js` の分野名と一致させます。
4. `choices` は 5〜8 個にします。
5. `answerIndex` は 0 始まりの添字にします。
6. `explanation` を必ず記述します。

## 問題データ形式

`data/schema.md` に JSON の形式と必須フィールドの説明があります。

## 保存・通信について

- このアプリはサーバーとの通信を行いません。
- 学習履歴や成績は保存しません。
- ページをリロードすると集計はリセットされます。

## 今後の拡張案

- 難易度指定機能の追加
- 間違えた問題だけ再出題するモード
- 画像やグラフ問題の対応
- PWA 化
- 教員用の問題編集画面

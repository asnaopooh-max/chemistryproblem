# 問題作成ガイド

このガイドは、化学基礎共通テスト対策アプリに新しい問題を追加するための手順と注意点をまとめたものです。

## 追加手順

1. `generate_questions.py` で下書き候補を作る。
2. `data/question_drafts.json` の内容を確認する。
3. 採用したい問題だけ `reviewStatus` を `approved` に変更する。
4. `generate_questions.py --promote data/question_drafts.json` で `data/questions.json` に採用する。
5. 手動で追加する場合は、末尾に新しい問題オブジェクトを追加する。
6. `id` は重複しないようにする。
7. `category` は `js/constants.js` の分野名と一致させる。
8. `difficulty` は 1〜5 の数値で設定する。
9. `choices` は 5〜8 個にする。
10. `answerIndex` は正解選択肢の 0 始まりの添字にする。
11. `explanation` を必ず記述する。
12. 必要なら `point` を追加する。

## 下書き生成ワークフロー

`generate_questions.py` は本番の `data/questions.json` を直接増やさず、まず下書きファイルを作るためのツールです。
実行には Python 3 が必要です。

```powershell
python generate_questions.py --count 80
python generate_questions.py --check data/question_drafts.json
```

採用する問題だけ、下書き内の `reviewStatus` を `approved` に変更します。

```json
"reviewStatus": "approved"
```

その後、次のコマンドで採用します。

```powershell
python generate_questions.py --promote data/question_drafts.json
```

生成ツールは、似た問題の量産を避けるため、問題ファミリーごとの上限、類似問題文の検出、正解位置の偏り確認、分野・技能の分布確認を行います。

## 問題作成のポイント

- 共通テスト対策として、基本から標準レベルの問題を中心にする。
- 文章をわかりやすくし、読みやすい日本語を心がける。
- 問題文に図や表が必要な場合は `extra` フィールドに簡単な説明やデータを追加できる。
- 正解の根拠を `explanation` に書き、学習ポイントがあれば `point` に補足する。
- `choices` の順序は、難易度に応じて簡単な選択肢から配置してもよい。

## 良問化のチェック観点

- 同じ数値差し替え問題を続けすぎない。
- `知識`、`理解`、`計算`、`判断`、`読解` を混ぜる。
- 1つの分野だけに偏らせない。
- 選択肢は、明らかに不自然なものだけで埋めない。
- 誤答選択肢にも「なぜ間違えやすいか」があるようにする。
- 解説は正答だけでなく、考え方が残る文章にする。
- 実験・グラフ問題では、条件、単位、読み取る量を明確にする。

## 例

```json
{
  "id": "CB-023",
  "category": "酸と塩基",
  "unit": "pH",
  "topic": "pH の計算",
  "difficulty": 3,
  "skill": "計算",
  "question": "水素イオン濃度が 1.0×10^-3 mol/L の溶液の pH はいくつか。",
  "choices": [
    "1",
    "2",
    "3",
    "4",
    "5"
  ],
  "answerIndex": 2,
  "explanation": "pH は -log[H+] で求める。-log10^-3 = 3 である。",
  "point": "pH は水素イオン濃度の対数で表される。"
}
```

## 共通テスト風の注意点

- 問題文は短く、設問に必要な情報を絞る。
- 選択肢は似たような値や表現が混ざる場合があるが、明確な正答があるようにする。
- 実験やグラフ問題では、条件や単位を丁寧に示す。
- 数式や化学式はテキスト表記で記述し、可能なら単位や濃度を明示する。

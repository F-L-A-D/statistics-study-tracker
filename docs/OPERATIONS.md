# 運用ルール

1. 出題前に `data/progress.json` を読み、未確認小論点を優先し、5問をできるだけ別分野から選ぶ。問題に論点IDを明記。
2. 採点時に論点ID・問題ID・難易度・○△×を記録し、同じ問題の再演習は累計問題数を増やさず既存評価を更新する。
3. `data/progress.json` の更新は最新blob SHAを取得してから実行。失敗時は成功と断言せず再確認する。
4. `counts` は過去116問の確定済み集計を基準とし、個別履歴未復元分を推測しない。新規問題のみtotal_questionsを増やす。
5. dashboard.htmlをスマホで開く場合は、GitHub上のJSONを端末へ保存してファイル選択で読み込む。GitHubのHTMLプレビューはアプリを実行しない。
6. GitHub Pagesの公開は無効のまま。認証付きWebアプリを将来構築する場合はサーバー側でトークンを管理し、HTMLに埋め込まない。


## Queue MVP (2026-10-21)

- 正本: `data/queue.json`（Queueの順序・状態）, `data/lesson-bank.json`（問題本文・正答）, `data/progress.json`（採点履歴）。`taxonomy.json` は単元IDを定義。
- 初期移行: 旧day 1〜10の50問を参照検証後、S0001〜S0010へ明示的に登録。旧50問を採点済み扱いにはしない。旧116問の集計、既存履歴は変更しない。
- pending/ready は未完了、consumed は完了。表示順は sequence 昇順。セットIDは再利用しない。 generated_at=null は旧教材の作成時刻不明を意味する。
- 補充: 原則3新規+2復習。復習候補は履歴の最新評価×→△→○。足りなければ新規で補完。出題済み未回答は評価を更新しない。新規問題には未使用の恒久IDを割り当てる。再演習は新しい試行IDでhistoryへ追記し、ユニーク問題数を増やさない。
- 消費トランザクション: ①5つの採点試行を履歴へ保存する準備 ②不足セット数に対応する補充教材を作成・検証 ③消費するセットをconsumedに変更しconsumed_at/consumption_idを付与 ④新セットを追加 ⑤ lesson-bank、progress、queueを **同一Gitコミット** に含め、mainの旧HEADを条件とする楽観ロックでref更新。いずれか失敗したらrefは更新しない。結果が不明ならHEAD・consumption_id・attempt_idを再取得して確定する。既存IDの再実行はno-opとする。
- 不変条件: 未完了10セット×5問。全question_idは問題バンクに存在。consumedセットの5問は該当セットの採点試行をprogressで参照可能。既存historyや集計を再集計だけで消去しない。
- 21時タスク: queue.jsonのpending/ready中、sequence最小のset_idを読み、practice.html?set=Sxxxx を案内する。タスクは自動補充機構ではない。
- 注意: **現時点で自動採点・自動生成・トランザクション実行のバックエンドは未実装**。GitHub Pagesは読み取り専用。セット消費を手動で行う際も上の同一コミット手順が必須。補充問題の供給がなければ消費を保留し、不正な10セット維持を装わない。

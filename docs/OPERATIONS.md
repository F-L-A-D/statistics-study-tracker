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


## SQLite教材マスタ（2026-10-21）
- **教材の正本**: `data/curriculum.sqlite3`。教材・論点・講義を編集する際はSQLiteのテーブルを更新する。 `data/lesson-bank.json`, `data/taxonomy.json`, `data/lectures.json` はGitHub Pages用の派生物であり、直接編集しない。
- **履歴の正本**: `data/progress.json`（SQLiteへ移行しない）。**Queue状態の正本**: `data/queue.json`。SQLiteからのビルドでこれらを上書きしない。
- 初期移行は `python scripts/curriculum.py init`。DBが存在する場合は上書きを拒否／既存DBを保持する。
- SQL修正後に `python scripts/curriculum.py build` で公開用JSONを生成し、`python scripts/curriculum.py verify` と `python scripts/test_queue.py` で検証する。
- `scripts/lecture_seed.json` は **初回ブートストラップ用**。DB作成後はこのファイルを修正してもDBに自動反映されない。正式な講義改訂はSQLiteへ行う。
- `lectures.review_status`: draft（初稿）, in_review（レビュー中）, approved（承認）, needs_revision（要改訂）。`draft` は品質保証済みの意味ではない。
- 初期50問は削除しない。active Queueは3セット×5問。旧S0004〜S0010はbacklogとして保持（採点済み／消費済みではない）。
- セット完了の運用: 外部採点後、5問分のquestion_id・固有attempt_id・answer・○△×をJSONファイルにまとめる。まず `python scripts/complete_set.py grades.json --dry-run` で検証、次に **Git作業ツリーがクリーンな環境** で `python scripts/complete_set.py grades.json --commit` を実行。progress.jsonとqueue.jsonを同一コミットにしてpushする。認証・接続不良またはpush失敗時は未完了としてHEADと履歴を再確認する。
- 補充は既存問題プールから原則新規3＋復習2を選び、復習候補は×→△→○。不足時は新規で補完。検証済み問題が尽きたら明示的に停止し、SQLiteに新問を登録する必要がある。ChatGPT定時タスク単体では書き込み・補充は行われない。
- 新規扱いの講義を演習前に表示。採点済み論点は演習後に補講欄を開く。講義閲覧だけではprogress.jsonを変更しない。
- GitHub Actions `build-curriculum.yml` は教材更新用。初期移行時にはSQLiteと公開JSONを生成してコミットした。以後はSQLiteを編集しただけでは自動起動しないため、workflow_dispatchまたは対応するワークフローの再実行を行い、生成物のコミットを確認する。

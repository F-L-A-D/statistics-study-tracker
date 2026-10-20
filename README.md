# Statistics Study Tracker

統計検定準1級（2027年改訂範囲）の学習管理。非公開リポジトリ。

- `data/progress.json`: 正本。178管理用小論点、累計116問（○42/△74/×0）。未確認を未学習とみなさない。
- `dashboard.html`: モバイル対応ダッシュボード。ファイル選択で最新のprogress.jsonを読み込む（ブラウザからprivate GitHubを無認証で直接読めないため）。
- `docs/OPERATIONS.md`: 採点と同期の運用手順。

**同期の限界**：ChatGPTの定時タスクとGitHubコネクタの間には、常時稼働する自動同期サービスはない。タスクが実行時にGitHubを読書きできるかは未検証。出題タスクにはGitHubを参照・更新する指示を追加するが、成功確認できない限り同期済みと扱わない。

**公開に関する注意**：GitHub Pagesはprivate repoからでもサイト自体が公開される場合があるため、このリポジトリではPagesを有効にしない。

# Python File Organizer

A small CLI tool to organize files into category folders by extension.  
拡張子に基づき、ファイルをカテゴリ別フォルダへ自動整理するCLIツールです。

## ✨ Features / 機能
- Dry-run preview (`--dry-run`) for safety / 事前プレビューで安全実行
- Auto-rename on collisions (`file (2).ext`) / 名前衝突時の自動リネーム
- Recursive scan & hidden control / 再帰スキャン・隠しファイル制御
- JSON rules for customization / JSONルールで柔軟にカスタム

## 🚀 Quick Start / クイックスタート
```bash
# Preview (safe) / プレビュー（安全）
python organizer.py --source ~/Downloads --dry-run

# Execute / 実行
python organizer.py --source ~/Downloads --yes

# Recursive & include hidden / 再帰・隠し含む
python organizer.py -s . --recursive --include-hidden --yes
```

## 🧰 Environment / 動作環境
- Python 3.9+ (standard library only)

## 🗂️ Repository Structure / 構成例
```
.
├─ organizer.py
├─ rules.example.json
├─ README.md
└─ screenshots/   # optional
```

## ⚙️ Custom Rules (JSON) / ルール設定
Generate a template:
```bash
python organizer.py --write-default-rules rules.json
```
Example:
```json
{
  ".pdf": "docs",
  ".docx": "docs",
  ".xlsx": "sheets",
  ".csv": "sheets",
  ".png": "images",
  ".jpg": "images",
  ".mp4": "video"
}
```

## 🧠 Design Notes / 設計のポイント
- **Safety-first**: dry-run + confirmation prompt to prevent mistakes  
  誤操作防止のため `--dry-run` と確認プロンプトを実装
- **Collision handling**: `file (2).ext` style auto-rename  
  同名ファイルの衝突を自動回避
- **Extensibility**: rules as JSON, easy to extend categories  
  ルールをJSON化し、用途に合わせて拡張可能
- **Hidden files**: excluded by default, opt-in via flag  
  隠しファイルは既定で除外、フラグで包含

## ✅ Testing / テスト（任意）
- Use `tempfile` to create a sandbox directory and assert move results.  
  `tempfile` を使い、移動結果を検証する簡易テストで動作確認可能。

## ⚠️ Limitations & Future Work / 制限と今後
- 規則は拡張子ベース。内容判定（MIME/マジックナンバー）は未対応  
- 改善案：日付別仕分け、サイズ閾値、拡張子の自動学習、ログ出力、GUI/Web化

## 📄 License / ライセンス
MIT

## 👤 Author
Akemi (Your GitHub handle)

# CyclesTooner

[English](README_en.md) | 日本語

**VRM や MMD のアバターなど、EEVEE 向けのシェーダーが設定されたアバターモデルを、Cycles でもトゥーン調にレンダリングできるようにする** Blender アドオンです。

MToon、VRToon、UnityToon のシェーダーは、EEVEE 専用の `Shader to RGB` ノードで陰影を作っているため、Cycles でレンダリングすると意図した見た目になりません。MMD（MMDShaderDev）も EEVEE での表示を前提に作られています。CyclesTooner は、これらのマテリアルを Blender 標準の **Toon BSDF** に置き換えます。テクスチャ・色・法線・透明度はできる限り引き継ぎます。さらに、Cycles で使える背面法のアウトラインを Geometry Nodes で生成します。

Cycles の反射、屈折、ボリューム、魚眼レンズなどを使ったシーンに、トゥーン調のキャラクターを置きたい場合に向いています。

## できること

- **マテリアル変換**：MToon（VRM Add-on for Blender）、MMDShaderDev（MMD Tools）、VRToon（VRToon Shader Manager）、UnityToon と Unlit（Unitypackage Importer）、Principled BSDF を Toon BSDF に変換します。
- **アウトライン生成**：モデル全体を囲む背面法アウトラインを作成します。頂点ウェイトで部分ごとの太さを調整できます。
- **一括調整**：変換済みマテリアルの Opacity（不透明度）と Smooth（陰影境界のぼかし）をまとめて変更できます。

## 動作環境

- Blender 5.2 LTS（推奨）／ 4.5 LTS 以上
- レンダラー：Cycles（アウトラインは Cycles 向けに調整されています）

## インストール

### 拡張機能リポジトリから（推奨）

リポジトリを登録すると、新しいバージョンが Blender 起動時に自動で検出され、そのまま更新できます。

1. Blender で `編集 (Edit)` > `プリファレンス (Preferences)` > `エクステンションを入手 (Get Extensions)` を開きます。
2. 右上の `リポジトリ (Repositories)` ドロップダウンから `[+]` > `リモートリポジトリを追加 (Add Remote Repository)` を選びます。
3. URL に次を入力します。
   ```
   https://utagestudio.github.io/CyclesTooner/index.json
   ```
4. `起動時に更新チェック (Check for Updates on Startup)` をオンにして追加します。
5. 一覧に表示された **CyclesTooner** の `インストール (Install)` を押します。

### ZIP ファイルから

オフライン環境などでリポジトリを登録できない場合の方法です。

1. [index.json](https://utagestudio.github.io/CyclesTooner/index.json) の `archive_url` に書かれた `cycles_tooner-<バージョン>.zip` をダウンロードします（`https://utagestudio.github.io/CyclesTooner/` の後ろにファイル名を付けた URL です）。
2. Blender で `編集 (Edit)` > `プリファレンス (Preferences)` > `エクステンションを入手 (Get Extensions)` を開きます。
3. 右上の `⌄` メニューから `ディスクからインストール... (Install from Disk...)` を選び、ダウンロードした ZIP を選びます。

GitHub の「Download ZIP」で取得したソースコードは、開発用のファイルを含むため、インストールには使わないでください。この方法では自動更新されません。

## クイックスタート

3D ビューポートのサイドバー（`N` キー）の **Tool** タブに **CyclesTooner** パネルがあります。

1. **変換前に .blend ファイルを保存します。**（[注意事項](#注意事項)を参照）
2. モデルの**ルート**（Armature や Empty など、一番上の親）を選び、**Convert** を押します。選んだオブジェクトとその子孫すべてのマテリアルが変換されます。
3. モデル内のどれか 1 つのオブジェクトを選び、**Add Outline** を押します。
4. Cycles でレンダリングします。必要に応じて Smooth、Opacity、アウトラインの色と太さを調整します。

## 注意事項

Convert と Add Outline は、シーンのデータを直接書き換えます。元の状態に戻す必要がありそうなら、事前に .blend ファイルを保存してください。

- **Convert は元のシェーダーを削除します。** MToon、MMDShaderDev、VRToon、UnityToon、Unlit から変換したマテリアルは、**Revert** しても元のシェーダーには戻らず、簡易的な Principled BSDF になります。
- **元のシェーダーの表現をすべて再現するわけではありません。** 陰影色、MatCap、リムライト、スペキュラー、発光などは Toon BSDF では再現されません（[対応シェーダー](#対応シェーダー)を参照）。
- **VRToon のアウトラインは Convert で削除されます。** 太さの情報は保存されるので、**Add Outline** を押すと CyclesTooner のアウトラインとして作り直せます。
- **Add Outline はオブジェクトの所属コレクションを変更します。** モデルの階層にあるすべてのオブジェクトが、新しく作られる `<ルート名>_Collection` に移動します。
- **レンダーエンジンは Cycles に切り替わります。** EEVEE を使っている状態で Convert を押すと、自動で Cycles に変更されます。
- 通常の Emission ノードや、Principled BSDF 以外の未対応のシェーダーは変換しません。

## 対応シェーダー

| 変換元 | 作成するアドオン | 引き継ぐもの | 再現しないもの |
| --- | --- | --- | --- |
| Principled BSDF | Blender 標準 | Base Color（色・テクスチャ）、Normal、Alpha | 金属・粗さ・スペキュラーなどの質感 |
| MToon | [VRM Add-on for Blender](https://vrm-addon-for-blender.info/ja-jp/) | ベーステクスチャの色と Alpha、UV 変換、Normal、Base Color、Alpha | Shade Color、MatCap、Rim、Emission、Outline |
| MMDShaderDev | [MMD Tools](https://extensions.blender.org/add-ons/mmd-tools/) | `mmd_base_tex` の色と Alpha、UV 変換、Normal、Diffuse Color、Alpha | Sphere テクスチャ、Toon テクスチャ |
| VRToon | [VRToon Shader Manager](https://kafuji.github.io/Sakura-Creative-Suite/ja/addons/VRToon_Shader_Manager/) | Base Color（色・テクスチャ）、Normal、Alpha と Material Alpha、アウトラインの太さ | 陰影、スペキュラー、リム、AO、マスク |
| UnityToon（v1） | [Unitypackage Importer](https://utagestudio.github.io/unitypackage_loader/ja/) | Base Color（テクスチャ・Tint・UV 変換を含む）、Normal、Alpha | 影、MatCap、リム、Emission |
| Unlit | [Unitypackage Importer](https://utagestudio.github.io/unitypackage_loader/ja/) | 色、テクスチャ、Alpha | — |

- 変換後の Toon BSDF は `Size: 0.8`、`Smooth: 0.2` で作成されます。
- 各アドオンは CyclesTooner に同梱されていません。色や透明度の一部は各アドオンのマテリアル設定から読み取るため、変換するときは、読み込みに使ったアドオンを有効にしておくことをおすすめします。
- VRToon は、名前が `VRToon` で始まるシェーダーグループが Material Output に接続されている場合に変換されます。UnityToon と Unlit は、Unitypackage Importer が作成した構成の場合だけ変換されます。
- VRChat 向けアバターでよく使われる lilToon や Poiyomi は、直接は変換できません。Unitypackage Importer で読み込んだあとのマテリアル（UnityToon・Unlit）が変換の対象です。

## 機能の詳細

### マテリアル変換

- **Convert**：選択したオブジェクトとその子孫のマテリアルを変換します。
  - 透明度は、Toon BSDF と Transparent BSDF を Mix Shader で合成する共通の仕組みで制御します。元のマテリアルの Alpha（テクスチャ・値）は、この仕組みに引き継がれます。
  - EEVEE とマテリアルプレビューでの表示が乱れないよう、マテリアルのレンダーメソッドを `Dithered` に設定します。Cycles の見た目には影響しません。
  - 変換後のノードは接続順に自動整列されます。用途を判断できない未接続のノードは削除せず、`CyclesTooner Preserved Nodes` フレームにまとめます。
- **Revert**：変換したマテリアルを Principled BSDF に戻します。変換元が Principled BSDF 以外の場合は、元のシェーダーではなく簡易的な Principled BSDF になります。
- **Opacity / Apply Opacity**：選択したオブジェクトとその子孫の変換済みマテリアルに、不透明度をまとめて設定します。`1.0` で不透明、`0.0` で完全に透明です。
- **Smooth / Apply Smooth**：同じ範囲の Toon BSDF の Smooth をまとめて設定します。値を上げると陰影の境界がやわらかくなります。
- **Material 欄**：アクティブなマテリアルが変換済みの場合、そのマテリアルだけの Opacity と Smooth を変更できます。

### アウトライン

- **Add Outline**：選択したオブジェクトの一番上の親（Empty を含む）をルートとして、モデル全体のアウトラインを作成します。次の構成が作られます。

  ```text
  <ルート名>_Collection
  ├─ <ルート名>（と子孫すべて）
  └─ <ルート名>_Outline_Collection
     ├─ <ルート名>_Outline          … アウトライン本体
     └─ <ルート名>_Outline_Source   … アウトラインの対象メッシュ（ビューレイヤーから除外）
  ```

  - アウトラインの対象は、レンダリングされるメッシュだけです。オブジェクトやコレクションでレンダー無効にしたメッシュは対象外です。ビューポートだけで非表示にしたメッシュは対象に含まれます。
  - アウトライン用のマテリアルはモデルごとに作られるので、モデルごとに色を変えられます。
  - アウトラインは選択できない設定になり、Cycles のディフューズ反射と影には写りません。
- **太さの調整**
  - 全体の太さは **Outline Thickness** と **Apply Outline Thickness** で変更します（初期値 `0.002`）。モディファイア `ToonOutlineGN` の `Thickness` でも変更できます。
  - 対象の各メッシュには頂点グループ `CT_Outline` が作られ、全頂点のウェイトが `0.5` に設定されます。ウェイトを塗り替えると、部分ごとに太さを変えられます。
  - `CT_Outline` がすでにある場合、そのウェイトは変更されません。
  - VRToon から変換したモデルでは、Convert 時に保存した太さとウェイトが使われます。
- **Outline Color / Apply Outline Color**：選択したモデルのアウトラインの色を変更します。
- **Refresh Outline**：モデルのパーツの表示・非表示を切り替えたあと、アウトラインの対象を作り直します。モデル内のオブジェクトか、アウトライン本体を選んでから押してください。色や太さの設定は保持されます。
- **Remove Outline**：アウトライン本体、対象コレクション、使われなくなったアウトライン用のデータを削除します。モデル内のオブジェクトか、アウトライン本体を選んでから押してください。

## トラブルシューティング

メッセージとツールチップは、Blenderの言語設定に合わせて日本語または英語で表示されます。

| 症状 | 対処 |
| --- | --- |
| Convert しても一部のマテリアルが変わらない | 変換されるのは選択したオブジェクトとその子孫だけです。モデルのルートを選んでください。未対応のシェーダーは変換されません（[対応シェーダー](#対応シェーダー)を参照）。 |
| 「このルートオブジェクトのアウトラインは既に存在します」と表示される | アウトラインは作成済みです。**Refresh Outline** で対象を更新するか、**Remove Outline** で削除してから作り直してください。 |
| 「アウトライン対象のレンダー対象メッシュが見つかりませんでした」と表示される | モデルの階層に、レンダリングされるメッシュがありません。オブジェクトとコレクションのレンダー表示設定を確認してください。 |
| パーツを非表示にしてもアウトラインが残る | **Refresh Outline** を押してください。 |
| VRToon のアウトラインが Convert 後に消えた | 仕様です。**Add Outline** を押すと、保存された太さで作り直されます。 |
| Revert しても元の見た目に戻らない | Principled BSDF 以外からの変換は、元のシェーダーに戻せません。変換前に保存した .blend ファイルを使ってください。 |

## お問い合わせ

不具合の報告、要望、質問は[お問い合わせフォーム](https://tally.so/r/kdVdDR?product=CyclesTooner)から送れます。
GitHub のアカウントをお持ちなら、[Issues](https://github.com/utagestudio/CyclesTooner/issues) に書いていただいてもかまいません。

## 開発者向け

- アドオンの動作仕様：[docs/behavior.md](docs/behavior.md)
- バージョン、ブランチ、コミット、リリースの運用：[VERSIONING.md](VERSIONING.md)

## ライセンス

[GPL-3.0-or-later](LICENSE)

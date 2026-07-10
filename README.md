# CyclesTooner - Blender Toon Shader Assistant

CyclesToonerは、Principled BSDF、MMD（mmd_shader）、VRM（MToon）といったシェーダーを、Cyclesで扱える Toon BSDF に簡易変換し、トゥーンレンダリング（セルルック）表現を効率的に行うためのBlenderアドオンです。  
あわせて、Cyclesレンダラーでも綺麗に表示できる「背面法」によるアウトライン自動生成機能も備えています。

## 機能概要

### 1. マテリアル変換 (Material Converter)
選択したオブジェクト（およびその子階層の全オブジェクト）のマテリアルを自動的に変換します。

*   **Convert**:
    *   `Principled BSDF` を `Toon BSDF` (Size: 0.8 / Smooth: 0.2) に置き換えます。
    *   MMD Tools の `MMDShaderDev` / `mmd_shader` 構成も直接 `Toon BSDF` に変換できます。
    *   VRM Add-on for Blender の `MToon` 構成も直接 `Toon BSDF` に変換できます。
    *   `Base Color` や `Normal` の接続は維持されます。
    *   透明度調整用のノードを自動で追加します（Mix Shader + Transparent BSDF）。
    *   `Alpha` に接続がある場合、Alpha入力とOpacity設定の両方を反映します。
    *   実行時、レンダリングエンジンが EEVEE の場合は自動的に **Cycles** に切り替わります。
*   **Revert**:
    *   CyclesToonerによって変換されたマテリアルを、元の `Principled BSDF` に戻します。
*   **Opacity**:
    *   サイドバーのスライダーから、選択オブジェクト（および子階層）のToon化済みマテリアルへ透明度を一括適用できます。
    *   アクティブオブジェクトのマテリアルがToon化済みの場合、マテリアル単位でも透明度を個別調整できます。
    *   `1.0` は不透明、`0.0` は完全透明です。
*   **Smooth**:
    *   サイドバーのスライダーから、選択オブジェクト（および子階層）のToon Smooth値を一括適用できます。
    *   アクティブオブジェクトのマテリアルがToon化済みの場合、マテリアル単位でもSmoothを個別調整できます。

### 2. アウトライン生成 (Outline Generator)
Cyclesレンダラーでのトゥーン表現に最適な「背面法」を用いたアウトライン用メッシュを自動生成します。

*   **Add Outline**:
    *   選択中オブジェクトの最上位親（Emptyを含む）配下のメッシュを参照するアウトライン用オブジェクトを作成します。
    *   ルート用コレクションを作成し、その中にルート配下の全オブジェクトとアウトライン管理コレクションを配置します。
    *   **Geometry Nodes** を使用し、元のモデルを法線方向にわずかに押し出して裏面を表示する仕組みです。
    *   非表示のメッシュオブジェクトはアウトライン対象から除外されます。
    *   **太さの調整**:
        *   頂点グループ（Vertex Group）のウェイト値で太さを制御できます（デフォルト: 0.5）。
        *   基本の太さ係数はモディファイア設定 (`Value`) で一括調整可能です。
    *   ビューポートでの選択不可（Selectable OFF）、CyclesのRay Visibility（Diffuse/Shadow OFF）設定も自動で行います。
*   **Remove Outline**:
    *   作成したアウトラインメッシュを削除します。
    *   不要になったGeometry Nodeグループやマテリアルも自動的にクリーンアップします。
*   **Refresh Outline**:
    *   モデルパーツ、または生成済みアウトラインを選択した状態でのみ、既存アウトラインの対象メッシュを現在の表示状態に合わせて更新します。

## インストール方法

### 拡張機能リポジトリからインストール（推奨・Blender 4.2以降）

リモートリポジトリとして登録すると、Blender起動時に更新が自動検出され、ワンクリックでアップデートできます。

1.  Blenderを開き、`編集 (Edit)` > `プリファレンス (Preferences)` > `エクステンションを入手 (Get Extensions)` を開きます。
2.  右上の `リポジトリ (Repositories)` ドロップダウンから `[+]` > `リモートリポジトリを追加 (Add Remote Repository)` を選択します。
3.  URLに以下を入力します:
    ```
    https://utagestudio.github.io/CyclesTooner/index.json
    ```
4.  **起動時に更新をチェック (Check for Updates on Startup)** にチェックを入れて追加します。
5.  拡張機能一覧に表示された **CyclesTooner** の `インストール (Install)` を押します。
6.  以降、新しいバージョンが公開されるとBlender起動時に検出され、`Get Extensions` 画面から `アップデート (Update)` できます。

### ZIPファイルからインストール（Blender 4.1以前）

1.  このリポジトリのファイルをZIP形式でダウンロードするか、フォルダごと用意します。
2.  Blenderを開き、`編集 (Edit)` > `プリファレンス (Preferences)` > `アドオン (Add-ons)` を開きます。
3.  `インストール (Install)` ボタンを押し、アドオンのファイル（またはZIP）を選択します。
4.  リストに表示された **"Material: CyclesTooner"** にチェックを入れて有効化します。

## 使い方

3Dビューポートのサイドバー（Nキー）にある **Tool** タブ内に **CyclesTooner** パネルが表示されます。

### マテリアルの変換
1.  変換したいオブジェクトを選択します（複数選択可）。
2.  **Convert** ボタンを押すと、マテリアルがトゥーン調に変換されます。
3.  **Opacity** / **Smooth** スライダーを調整し、**Apply Opacity** / **Apply Smooth** を押すと選択範囲のToonマテリアルへ一括適用されます。
4.  アクティブマテリアルがToon化済みの場合は、表示される **Material** 欄から個別にOpacity/Smoothを変更できます。
5.  元に戻したい場合は **Revert** ボタンを押します。

#### MMDShaderDev からの直接変換
MMD Tools で読み込まれた `mmd_shader` マテリアルは、**Convert** ボタンで直接 CyclesTooner 形式へ変換できます。

`mmd_base_tex` の画像色とAlpha、MMDマテリアルのDiffuse Colorを可能な範囲で引き継ぎます。MMDマテリアルのAlphaはCyclesToonerの **Opacity** 初期値として統合されます。変換時に `MMDShaderDev` 用ノードは削除されるため、**Revert** は簡易的な `Principled BSDF` への復元になり、元のMMDShaderDev構成は復元しません。Sphere/Toon texture合成の完全再現も対象外です。

#### MToon からの直接変換
VRM Add-on for Blender で読み込まれた `MToon` マテリアルは、**Convert** ボタンで直接 CyclesTooner 形式へ変換できます。

ベーステクスチャの画像色とAlpha、MToonのBase Colorを可能な範囲で引き継ぎます。MToonのAlphaはCyclesToonerの **Opacity** 初期値として統合されます。変換時に `MToon` 用ノードは削除されるため、**Revert** は簡易的な `Principled BSDF` への復元になり、元のMToon構成は復元しません。Shade Color、MatCap、Rim、Emission、OutlineなどのMToon固有表現の完全再現は対象外です。

### アウトラインの作成
1.  アウトラインを作成したいモデル内のオブジェクトを選択します。
2.  **Add Outline** ボタンを押します。
    *   選択オブジェクトの最上位親をルートとして、その配下だけがアウトライン対象になります。
    *   ルートと同じ階層に `～_Collection` が生成され、その中にルート配下の全オブジェクトが移動します。
    *   `～_Collection` の中に `～_Outline_Collection` が生成されます。
    *   `～_Outline_Collection` の中に `～_Outline` オブジェクトと、非表示メッシュを除外するための `～_Outline_Source` コレクションが作成されます。
3.  モデルパーツの表示・非表示を切り替えた場合は、対象パーツまたは生成済みアウトラインを選択して **Refresh Outline** ボタンでアウトライン対象を更新します。
4.  アウトラインの太さを頂点ウェイトで調整したい場合は、Modifiers の `ToonOutlineGN` の `Weight` にある「Input Attribute Toggle」をクリックし、ウェイト情報のある頂点ウェイト名を記載してください。
5.  削除したい場合は、生成されたアウトラインオブジェクト、または元のコレクションを選択して **Remove Outline** ボタンを押します。

## 動作環境
*   Blender 5.0 (推奨) / 3.0以上
*   推奨レンダラー: **Cycles** (アウトライン機能はCyclesの仕様に最適化されています)

## LICENSE
[GPL-3.0-or-later](LICENSE)

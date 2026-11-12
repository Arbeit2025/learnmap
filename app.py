# -*- coding: utf-8 -*-
"""
learnmap - テーマを入力すると学習マップ（知識のつながり）を表示するツール。

単一ファイル Flask アプリ。知識ベースはこのファイル内の KB に持つ。
登録外のテーマは汎用テンプレート（5段階）を生成して返す。
"""
from urllib.parse import quote

from flask import Flask, redirect, render_template_string, request, url_for, abort

app = Flask(__name__)

STAGES = ["前提", "基礎", "核心", "応用", "実践"]
WIKI = "https://ja.wikipedia.org/wiki/"


def N(title, stage, desc, links):
    """ノード定義。links は (ラベル, URL) のリスト。"""
    return {"title": title, "stage": stage, "desc": desc, "links": links}


def W(article, label=None):
    """Wikipedia 記事へのリンクを作る。"""
    return (label or ("Wikipedia「%s」" % article), WIKI + article)


# ---------------------------------------------------------------------------
# 知識ベース: テーマ -> ノード列（順序がそのまま学習の流れになり、前のノードと線でつながる）
# ---------------------------------------------------------------------------
KB = {
    "Python": [
        N("プログラミングとは", "前提", "コンピュータに手順を指示する考え方。言語ごとの違いと共通点を押さえる。", [W("プログラミング"), W("Python")]),
        N("インストールと実行", "前提", "Pythonを入れて、対話モードとスクリプト実行を試すところから始める。", [("公式サイト", "https://www.python.org/"), ("公式チュートリアル", "https://docs.python.org/ja/3/tutorial/index.html")]),
        N("変数とデータ型", "基礎", "数値・文字列・真偽値などの型と、変数への代入・演算を学ぶ。", [("公式チュートリアル（データ構造の前段）", "https://docs.python.org/ja/3/tutorial/introduction.html")]),
        N("条件分岐と繰り返し", "基礎", "if文とfor/while文で処理の流れを制御できるようにする。", [("公式チュートリアル（制御フロー）", "https://docs.python.org/ja/3/tutorial/controlflow.html")]),
        N("リストと辞書", "基礎", "複数のデータをまとめて扱う代表的なコンテナ型を使いこなす。", [("公式チュートリアル（データ構造）", "https://docs.python.org/ja/3/tutorial/datastructures.html")]),
        N("関数", "核心", "処理を名前付きの部品にまとめ、再利用と見通しを良くする。", [("公式チュートリアル（関数の定義）", "https://docs.python.org/ja/3/tutorial/controlflow.html#defining-functions")]),
        N("クラスとオブジェクト指向", "核心", "データと振る舞いをひとまとめにするクラス設計の基礎。", [W("オブジェクト指向"), ("公式チュートリアル（クラス）", "https://docs.python.org/ja/3/tutorial/classes.html")]),
        N("ファイル操作と例外処理", "核心", "ファイルの読み書きと、エラーに備える try/except を身につける。", [("公式チュートリアル（入出力）", "https://docs.python.org/ja/3/tutorial/inputoutput.html"), ("公式チュートリアル（エラーと例外）", "https://docs.python.org/ja/3/tutorial/errors.html")]),
        N("ライブラリ活用", "応用", "標準ライブラリと外部パッケージ（requests等）でできることを広げる。", [("標準ライブラリ", "https://docs.python.org/ja/3/library/index.html"), W("ライブラリ")]),
        N("小さなアプリを作る", "実践", "題材を決めて、動くものを最後まで作り切る。公開まで行うと定着する。", [W("プロトタイプ")]),
    ],
    "Web開発": [
        N("インターネットとWebの仕組み", "前提", "ブラウザとサーバーの役割、URLやDNSの基本を押さえる。", [W("World Wide Web"), ("MDN Web Docs", "https://developer.mozilla.org/ja/docs/Learn")]),
        N("HTMLの基礎", "基礎", "文書の構造をタグで表す。見出し・段落・リンク・画像が中心。", [("MDN: HTML", "https://developer.mozilla.org/ja/docs/Learn/HTML")]),
        N("CSSの基礎", "基礎", "色・余白・配置など見た目を整える。セレクタとボックスモデルが要点。", [("MDN: CSS", "https://developer.mozilla.org/ja/docs/Learn/CSS")]),
        N("JavaScriptの基礎", "核心", "ページに動きを付ける言語。変数・関数・イベント処理から始める。", [("MDN: JavaScript", "https://developer.mozilla.org/ja/docs/Learn/JavaScript")]),
        N("ブラウザとDOM", "核心", "HTMLを木構造として操作する仕組みと、開発者ツールの使い方。", [W("Document Object Model"), ("MDN: DOM", "https://developer.mozilla.org/ja/docs/Web/API/Document_Object_Model")]),
        N("HTTPとAPI", "核心", "リクエストとレスポンス、JSON形式のAPI連携の基本。", [W("Hypertext Transfer Protocol"), ("MDN: HTTP", "https://developer.mozilla.org/ja/docs/Web/HTTP")]),
        N("フレームワーク入門", "応用", "FlaskやReactなど、開発を助ける枠組みの役割を理解する。", [W("Webアプリケーションフレームワーク")]),
        N("データベース連携", "応用", "データを保存・検索する仕組みと、SQLの初歩。", [W("データベース"), W("SQL")]),
        N("公開・デプロイ", "実践", "作ったサイトをインターネットに公開し、運用する手順。", [W("デプロイ")]),
    ],
    "機械学習": [
        N("数学・統計の前提", "前提", "線形代数と確率・統計の最小限を先に押さえると後が楽になる。", [W("機械学習"), W("線形代数学")]),
        N("Pythonとデータ処理", "前提", "NumPyやpandasでデータを読み込み、整形できるようにする。", [("NumPy", "https://numpy.org/"), ("pandas", "https://pandas.pydata.org/")]),
        N("機械学習とは", "基礎", "データから規則を学ぶ仕組み。教師あり・なし学習の違いを知る。", [W("機械学習"), W("教師あり学習")]),
        N("回帰と分類", "基礎", "数値を予測する回帰と、種類を分ける分類という2大タスク。", [W("回帰分析"), W("分類 (統計学)")]),
        N("モデルの評価", "核心", "訓練用とテスト用に分け、精度などの指標で性能を測る。", [W("交差検証"), ("scikit-learn: モデル評価", "https://scikit-learn.org/stable/model_selection.html")]),
        N("過学習と正則化", "核心", "訓練データに合わせすぎる問題と、その抑え方。", [W("過学習"), W("正則化")]),
        N("ニューラルネットワーク", "応用", "層を重ねたモデルで複雑なパターンを学ぶ仕組み。", [W("ニューラルネットワーク"), W("パーセプトロン")]),
        N("深層学習フレームワーク", "応用", "PyTorchやTensorFlowで実際にモデルを組む。", [("PyTorch", "https://pytorch.org/"), ("TensorFlow", "https://www.tensorflow.org/")]),
        N("モデルを公開する", "実践", "学習済みモデルをAPIやアプリに組み込んで使える形にする。", [W("MLOps")]),
    ],
    "データ分析": [
        N("データとは何か", "前提", "数値・カテゴリなどデータの種類と、表形式データの見方。", [W("データ")]),
        N("表計算の基礎", "前提", "Excelやスプレッドシートで集計・並べ替え・グラフ化を試す。", [W("表計算ソフト")]),
        N("Pythonとpandas", "基礎", "DataFrameでデータを読み込み、絞り込みや集計を行う。", [("pandas ドキュメント", "https://pandas.pydata.org/docs/")]),
        N("データの前処理", "基礎", "欠損値や表記ゆれを整え、分析できる形にする地味だが要の工程。", [W("データクリーニング")]),
        N("集計と可視化", "核心", "グループ集計とグラフで傾向を読み取る。", [W("データ可視化"), ("matplotlib", "https://matplotlib.org/")]),
        N("統計の基礎", "核心", "平均・中央値・ばらつきなど、データを要約する指標。", [W("記述統計学")]),
        N("仮説検定", "応用", "差があると言えるかを確率で判断する考え方。", [W("統計的仮説検定")]),
        N("ダッシュボード作成", "応用", "指標を継続的に見られる形にまとめる。", [W("ダッシュボード")]),
        N("分析レポートを書く", "実践", "問い→分析→結論→提案の流れで伝わる形にまとめる。", [W("データ分析")]),
    ],
    "英語": [
        N("英語の音と発音", "前提", "発音記号と音の仕組みを知ると、聞き取りと発音が連動して伸びる。", [W("英語の発音"), W("国際音声記号")]),
        N("基本文法", "基礎", "文型と時制を中心に、英文の骨組みを理解する。", [W("英語の文法"), W("文型")]),
        N("頻出単語", "基礎", "日常と学習でよく出る単語から覚える。例文とセットで。", [W("英単語")]),
        N("リスニング", "核心", "音の変化に慣れ、意味のまとまりで聞き取る練習。", [W("リスニング")]),
        N("リーディング", "核心", "精読と速読を使い分け、長文に慣れる。", [W("速読")]),
        N("スピーキング", "応用", "型のある表現を口に出し、会話の往復に慣れる。", [W("スピーキング")]),
        N("ライティング", "応用", "文と文のつなぎ方を学び、短い文章から書く。", [W("ライティング")]),
        N("試験対策", "実践", "TOEICや英検など、目標の形式に合わせた対策。", [W("TOEIC"), W("実用英語技能検定")]),
        N("英語で仕事・交流", "実践", "メールや会議、日常会話など実場面で使い続ける。", [W("ビジネス英語")]),
    ],
    "数学": [
        N("数の性質", "前提", "素数や約数など、数の基本的な性質から。", [W("数"), W("素数")]),
        N("方程式と関数", "基礎", "未知数を求める方程式と、対応関係を表す関数の考え方。", [W("方程式"), W("関数 (数学)")]),
        N("図形と幾何", "基礎", "三角形や円など図形の性質と証明の進め方。", [W("幾何学"), W("ユークリッド幾何学")]),
        N("三角関数", "核心", "角度と辺の比を結ぶ関数。波の記述にもつながる。", [W("三角関数")]),
        N("微分", "核心", "変化の割合を捉える考え方。接線の傾きから入る。", [W("微分")]),
        N("積分", "核心", "細かく分けて合計する考え方。面積や体積と結びつく。", [W("積分")]),
        N("線形代数", "応用", "ベクトルと行列で、連立方程式や変換を扱う。", [W("線形代数学"), W("行列")]),
        N("確率", "応用", "偶然の出来事を数で表し、期待値などを考える。", [W("確率")]),
        N("数学で問題を解く", "実践", "既知の道具を組み合わせて未知の問題に当たる練習。", [W("数学")]),
    ],
    "統計学": [
        N("データの種類", "前提", "質的・量的データ、尺度の違いを知る入口。", [W("尺度水準")]),
        N("平均とばらつき", "基礎", "代表値と散らばりを表す基本の指標。", [W("平均"), W("標準偏差")]),
        N("グラフで表す", "基礎", "ヒストグラムや箱ひげ図で分布の形を見る。", [W("ヒストグラム"), W("箱ひげ図")]),
        N("確率の基礎", "核心", "場合の数と確率の計算の土台。", [W("確率論")]),
        N("確率分布", "核心", "正規分布など、値の出やすさを表すモデル。", [W("確率分布"), W("正規分布")]),
        N("推定", "応用", "標本から全体の姿を区間とともに推し量る。", [W("推定 (統計学)"), W("信頼区間")]),
        N("仮説検定", "応用", "仮説とデータの食い違いを確率で評価する手順。", [W("統計的仮説検定"), W("p値")]),
        N("回帰分析", "実践", "変数同士の関係を式で表し、予測や解釈に使う。", [W("回帰分析")]),
    ],
    "物理学": [
        N("力と運動", "前提", "速度・加速度とニュートンの運動法則から入る。", [W("ニュートン力学"), W("力 (物理学)")]),
        N("エネルギー", "基礎", "仕事とエネルギーの保存という見方を身につける。", [W("エネルギー"), W("運動エネルギー")]),
        N("波と音・光", "基礎", "波の性質と、音・光への応用。", [W("波動"), W("音"), W("光")]),
        N("電気と磁気", "核心", "電荷・電流・磁場の関係と回路の基礎。", [W("電磁気学"), W("電流")]),
        N("熱力学", "核心", "温度と熱、エネルギーの移り変わりの法則。", [W("熱力学"), W("エントロピー")]),
        N("原子と量子", "応用", "ミクロな世界の不思議な振る舞いへの入口。", [W("量子力学"), W("原子")]),
        N("相対性理論入門", "応用", "時間と空間が絶対ではないという考え方。", [W("相対性理論")]),
        N("実験と観測", "実践", "測る・比べる・記録するという物理の進め方を体験する。", [W("物理学")]),
    ],
    "化学": [
        N("原子と分子", "前提", "物質を粒子の集まりとして捉える出発点。", [W("原子"), W("分子")]),
        N("周期表", "基礎", "元素の並び方に込められた規則性を読む。", [W("周期表"), W("元素")]),
        N("化学結合", "基礎", "原子同士がどう結びつくか（共有・イオン・金属結合）。", [W("化学結合")]),
        N("化学反応と式", "核心", "反応を式で表し、量の関係を計算する。", [W("化学反応"), W("モル")]),
        N("酸と塩基", "核心", "pHと中和を中心に、水溶液の性質を扱う。", [W("酸と塩基"), W("水素イオン指数")]),
        N("有機化学入門", "応用", "炭素骨格を持つ化合物のグループ分けと性質。", [W("有機化学"), W("官能基")]),
        N("化学平衡", "応用", "反応が止まって見える状態と、そのずれ方。", [W("化学平衡")]),
        N("実験の基本操作", "実践", "安全に配慮した器具の扱いと観察・記録の作法。", [W("化学")]),
    ],
}
KB.update({
    "歴史": [
        N("時代区分と年表", "前提", "古代・中世・近世・近代という大きな区切りと年表の読み方。", [W("時代区分"), W("歴史")]),
        N("古代文明", "基礎", "メソポタミア・エジプト・中国など文明の起こり。", [W("文明"), W("古代オリエント")]),
        N("中世の世界", "基礎", "封建社会や宗教が中心だった時代の各地の姿。", [W("中世")]),
        N("近代国家の成立", "核心", "絶対王政から市民革命へ、国のかたちが変わる流れ。", [W("市民革命"), W("フランス革命")]),
        N("産業革命", "核心", "技術と産業の変化が社会をどう変えたか。", [W("産業革命")]),
        N("二つの世界大戦", "応用", "世界規模の戦争と国際秩序の変化。", [W("第一次世界大戦"), W("第二次世界大戦")]),
        N("冷戦と現代", "応用", "冷戦からグローバル化へ、現在につながる流れ。", [W("冷戦"), W("グローバリゼーション")]),
        N("史料を読む", "実践", "一次史料に触れ、書かれ方そのものを考える読み方。", [W("史料"), W("歴史学")]),
    ],
    "デザイン": [
        N("デザインとは", "前提", "見た目の装飾ではなく、目的のための設計だという視点。", [W("デザイン"), W("グラフィックデザイン")]),
        N("色彩の基礎", "基礎", "色相・明度・彩度と、配色の基本パターン。", [W("色彩"), W("配色")]),
        N("タイポグラフィ", "基礎", "書体選びと文字の組み方で読みやすさが変わる。", [W("タイポグラフィ")]),
        N("レイアウトと余白", "核心", "配置・整列・余白で情報の優先度を伝える。", [W("レイアウト"), W("余白")]),
        N("図形とアイコン", "核心", "単純な形で意味を伝える視覚言語の作り方。", [W("アイコン"), W("ピクトグラム")]),
        N("UIデザイン", "応用", "画面の使いやすさを設計する考え方と原則。", [W("ユーザーインターフェース"), W("ユーザビリティ")]),
        N("デザインツール操作", "応用", "Figmaなどの基本操作と、共同編集の流れ。", [("Figma", "https://www.figma.com/")]),
        N("ポートフォリオ制作", "実践", "作品を選び、意図が伝わる形にまとめて公開する。", [W("ポートフォリオ")]),
    ],
    "写真": [
        N("カメラの仕組み", "前提", "光を取り込んで記録するまでの基本原理。", [W("カメラ"), W("写真")]),
        N("露出の三要素", "基礎", "絞り・シャッター速度・ISOの組み合わせで明るさを決める。", [W("露出 (写真)"), W("絞り (光学)")]),
        N("構図", "基礎", "三分割法など、画面の中の配置の型を覚える。", [W("構図"), W("三分割法")]),
        N("レンズと焦点距離", "核心", "広角・標準・望遠で写り方がどう変わるか。", [W("レンズ"), W("焦点距離")]),
        N("光とライティング", "核心", "光の向きと質を見て、被写体の見え方を操る。", [W("ライティング")]),
        N("ジャンル別撮影", "応用", "風景・ポートレート・スナップなど目的別の工夫。", [W("ポートレート"), W("風景写真")]),
        N("現像とレタッチ", "応用", "RAW現像と、やりすぎない補正の考え方。", [W("RAW画像"), W("画像編集")]),
        N("作品を発表する", "実践", "SNSや写真展など、人に見せる場で学ぶ段階。", [W("写真家")]),
    ],
    "動画編集": [
        N("動画の基礎知識", "前提", "解像度・フレームレート・コーデックなど用語の整理。", [W("動画"), W("フレームレート")]),
        N("撮影の基本", "前提", "編集しやすい素材を撮るための画角と安定感。", [W("映像")]),
        N("編集ソフトの操作", "基礎", "タイムラインと素材管理など、共通の基本操作。", [W("ノンリニア編集")]),
        N("カット編集", "基礎", "不要部分を切り、つなぎ目を自然にする中心技術。", [W("カット (映像)")]),
        N("テロップと音", "核心", "文字情報とBGM・効果音で伝わり方が大きく変わる。", [W("テロップ"), W("音響効果")]),
        N("色調補正", "核心", "明るさと色を揃え、狙った雰囲気に近づける。", [W("カラーグレーディング")]),
        N("演出と構成", "応用", "起承転結と間（ま）で視聴者を離さない工夫。", [W("モンタージュ")]),
        N("書き出しと投稿", "実践", "媒体に合った設定で書き出し、公開して反応を見る。", [W("動画共有サービス")]),
    ],
    "音楽理論": [
        N("音と楽譜", "前提", "音の高さ・長さと、五線譜の読み方の入口。", [W("楽譜"), W("音高")]),
        N("音階と調", "基礎", "メジャーとマイナーの音の並びと調号。", [W("音階"), W("調 (音楽)")]),
        N("リズムと拍子", "基礎", "拍子とリズムパターンで音楽の骨格を作る。", [W("リズム"), W("拍子")]),
        N("コード（和音）", "核心", "三和音の成り立ちと、コードネームの読み方。", [W("和音"), W("三和音")]),
        N("コード進行", "核心", "定番の進行と、曲の流れの作り方。", [W("コード進行")]),
        N("メロディの作り方", "応用", "音階の音で旋律を組み立てる考え方とモチーフ。", [W("旋律")]),
        N("編曲入門", "応用", "楽器の役割分担と、音の重ね方。", [W("編曲")]),
        N("曲を作ってみる", "実践", "短い曲を最後まで作り、録音して聴き返す。", [W("作曲")]),
    ],
    "料理": [
        N("包丁と火加減", "前提", "道具の扱いと、安全・衛生の基本から。", [W("包丁"), W("調理")]),
        N("調味料の基本", "前提", "「さしすせそ」を中心に、味付けの主役たち。", [W("調味料"), W("さしすせそ")]),
        N("だしと味付け", "基礎", "うま味の土台と、味見しながら整える感覚。", [W("出汁"), W("うま味")]),
        N("炒める・煮る・焼く", "基礎", "基本の加熱調理それぞれのコツ。", [W("炒め物"), W("煮物"), W("焼き物 (料理)")]),
        N("献立の立て方", "核心", "主菜・副菜・汁物の組み立てと栄養バランス。", [W("献立")]),
        N("食材の下処理", "核心", "下ごしらえで仕上がりが変わる理由と手順。", [W("下ごしらえ")]),
        N("盛り付け", "応用", "器選びと配置でおいしさの印象を上げる。", [W("盛り付け")]),
        N("レパートリーを増やす", "実践", "得意料理を軸に、応用で幅を広げていく。", [W("料理")]),
    ],
    "簿記": [
        N("簿記とは", "前提", "取引を記録する仕組みと、学ぶと何が分かるか。", [W("簿記"), W("複式簿記")]),
        N("仕訳の基本", "基礎", "借方・貸方の考え方と、取引の分解のしかた。", [W("仕訳"), W("借方")]),
        N("勘定科目", "基礎", "資産・負債・収益・費用の代表的な科目を覚える。", [W("勘定科目")]),
        N("帳簿の記入", "核心", "仕訳帳から総勘定元帳への転記の流れ。", [W("総勘定元帳")]),
        N("試算表", "核心", "記録の正しさを確かめる集計表の作り方と見方。", [W("試算表")]),
        N("決算整理", "応用", "減価償却など、期末に行う調整の処理。", [W("決算"), W("減価償却")]),
        N("財務諸表の読み方", "応用", "貸借対照表と損益計算書から状態を読む。", [W("財務諸表")]),
        N("日商簿記3級対策", "実践", "過去問形式で解き、弱点を洗い出す段階。", [W("日商簿記検定")]),
    ],
    "会計": [
        N("会計とは", "前提", "お金の動きを記録し、報告する仕組み全体像。", [W("会計"), W("財務会計")]),
        N("財務諸表の全体像", "基礎", "主要な表がそれぞれ何を表すかの地図を持つ。", [W("財務諸表")]),
        N("損益計算書", "基礎", "期間の収益と費用から利益を読む。", [W("損益計算書")]),
        N("貸借対照表", "核心", "ある時点の財産の状態を左右のバランスで読む。", [W("貸借対照表")]),
        N("キャッシュフロー", "核心", "利益と現金のズレに注目する見方。", [W("キャッシュ・フロー計算書")]),
        N("原価計算", "応用", "製品やサービスにかかるコストの集計方法。", [W("原価計算")]),
        N("会計基準と監査", "応用", "ルールとチェックの仕組みで信頼性を担保する。", [W("会計基準"), W("監査")]),
        N("決算書で企業分析", "実践", "実在の決算書を読み比べ、指標で評価する。", [W("財務分析")]),
    ],
    "マーケティング": [
        N("マーケティングとは", "前提", "売る仕組みづくり全体を指す言葉だという理解。", [W("マーケティング")]),
        N("市場と顧客", "基礎", "誰に届けるかを分けて考えるセグメンテーション。", [W("市場細分化"), W("ターゲティング")]),
        N("4Pの基礎", "基礎", "製品・価格・流通・販促の4要素。", [W("マーケティングミックス"), W("4P")]),
        N("消費者心理", "核心", "人が買うまでの心理の流れと意思決定のクセ。", [W("消費者行動")]),
        N("ブランディング", "核心", "選ばれる理由として心に残るイメージを作る。", [W("ブランド"), W("ブランディング")]),
        N("デジタルマーケティング", "応用", "Web広告や検索など、オンライン施策の全体像。", [W("デジタルマーケティング"), W("検索エンジン最適化")]),
        N("SNSと広告", "応用", "SNSの特性に合わせた発信と広告の考え方。", [W("ソーシャルメディアマーケティング")]),
        N("施策の企画と検証", "実践", "仮説→実行→数値で振り返る回し方。", [W("PDCAサイクル")]),
    ],
})
KB.update({
    "心理学": [
        N("心理学とは", "前提", "心と行動を科学的に扱う学問だという位置づけ。", [W("心理学")]),
        N("知覚と認知", "基礎", "見聞きした情報を脳がどう処理するか。", [W("知覚"), W("認知")]),
        N("学習と記憶", "基礎", "覚える・忘れるの仕組みと条件づけ。", [W("記憶"), W("古典的条件づけ")]),
        N("発達心理学", "核心", "子どもから大人へ、心の育ちの段階。", [W("発達心理学")]),
        N("性格と個人差", "核心", "性格を捉える考え方と知能の個人差。", [W("性格"), W("ビッグファイブ (心理学)")]),
        N("社会心理学", "応用", "他人の存在が行動に与える影響（同調など）。", [W("社会心理学"), W("同調")]),
        N("臨床心理学入門", "応用", "心の不調への理解と支援の考え方の入口。", [W("臨床心理学"), W("心理療法")]),
        N("実験と調査法", "実践", "アンケートや実験でデータを取る作法。", [W("心理学研究法")]),
    ],
    "経済学": [
        N("需要と供給", "前提", "値段がどう決まるかの出発点になる考え方。", [W("需要と供給")]),
        N("市場と価格", "基礎", "競争や独占など、市場の形で結果が変わる。", [W("市場"), W("価格")]),
        N("GDPと経済指標", "基礎", "景気を測る代表的な数字の意味を知る。", [W("国内総生産"), W("経済指標")]),
        N("金融と金利", "核心", "お金の貸し借りと金利、中央銀行の役割。", [W("金融"), W("金利"), W("中央銀行")]),
        N("財政と税金", "核心", "政府の収入と支出が経済に与える影響。", [W("財政"), W("税")]),
        N("貿易と為替", "応用", "国同士の取引と通貨の交換レート。", [W("貿易"), W("外国為替")]),
        N("行動経済学", "応用", "人は必ずしも合理的ではないという視点。", [W("行動経済学")]),
        N("ニュースを経済で読む", "実践", "指標の発表や政策のニュースを読み解く練習。", [W("経済学")]),
    ],
    "法律入門": [
        N("法とは何か", "前提", "社会のルールとしての法の役割と種類。", [W("法"), W("法源")]),
        N("憲法の基礎", "基礎", "国の基本ルールと基本的人権の考え方。", [W("日本国憲法"), W("基本的人権")]),
        N("民法の基礎", "基礎", "人と人の関係を定める私法の中心。", [W("民法 (日本)")]),
        N("契約と権利", "核心", "約束が法的に守られる仕組み。", [W("契約"), W("権利")]),
        N("刑法の基礎", "核心", "犯罪と刑罰を定める法の目的と原則。", [W("刑法"), W("罪刑法定主義")]),
        N("会社法入門", "応用", "会社の成り立ちと運営のルール。", [W("会社法"), W("株式会社")]),
        N("労働法の基礎", "応用", "働く人を守るルールの全体像。", [W("労働法"), W("労働基準法")]),
        N("判例を読む", "実践", "裁判所の判断を読み、理由の組み立てを追う。", [W("判例")]),
    ],
    "哲学": [
        N("哲学とは", "前提", "当たり前を問い直す営みだという入口。", [W("哲学")]),
        N("古代ギリシャ哲学", "基礎", "ソクラテス・プラトン・アリストテレスの問い。", [W("古代ギリシア哲学"), W("ソクラテス")]),
        N("論理学の基礎", "基礎", "議論の正しさを確かめる道具立て。", [W("論理学"), W("三段論法")]),
        N("認識論", "核心", "「知っている」とはどういうことかを問う分野。", [W("認識論")]),
        N("倫理学", "核心", "善悪や正しさをめぐる代表的な考え方。", [W("倫理学"), W("功利主義")]),
        N("近代哲学", "応用", "デカルトやカントによる考え方の転回。", [W("近代哲学"), W("イマヌエル・カント")]),
        N("現代哲学とAI倫理", "応用", "言語や技術をめぐる現代の問い。", [W("人工知能の倫理")]),
        N("対話と議論", "実践", "相手の主張を聞き、自分の考えを組み立て直す練習。", [W("対話"), W("ディベート")]),
    ],
    "プログラミング基礎": [
        N("コンピュータの仕組み", "前提", "CPU・メモリ・入出力という基本構成を知る。", [W("コンピュータ"), W("中央処理装置")]),
        N("アルゴリズムとは", "前提", "問題を解く手順を明確にする考え方。", [W("アルゴリズム"), W("フローチャート")]),
        N("変数と型", "基礎", "データを名前付きで扱い、種類で区別する仕組み。", [W("変数 (プログラミング)"), W("データ型")]),
        N("制御構文", "基礎", "分岐と繰り返しで処理の流れを作る。", [W("制御構造")]),
        N("関数と分割", "核心", "処理を部品に分けて見通しを良くする。", [W("関数 (プログラミング)"), W("サブルーチン")]),
        N("データ構造", "核心", "配列・リスト・辞書など、データの並べ方の型。", [W("データ構造"), W("配列")]),
        N("デバッグ", "応用", "誤りの原因を切り分けて直す進め方。", [W("デバッグ"), W("バグ")]),
        N("小さなプログラムを作る", "実践", "題材を決めて動くものを完成させる経験が要。", [W("プログラミング")]),
    ],
    "文章術": [
        N("文章の目的と読者", "前提", "誰に何を伝えるかを先に決める出発点。", [W("文章"), W("ライティング")]),
        N("文の組み立て", "基礎", "主語と述語、一文を短く保つ基本。", [W("文"), W("主語")]),
        N("段落の作り方", "基礎", "一つの段落に一つの話題という型。", [W("段落")]),
        N("論理のつながり", "核心", "接続詞と順序で、読み手が迷わない流れに。", [W("論理"), W("接続詞")]),
        N("推敲と校正", "核心", "書いた後に整える工程で質が大きく変わる。", [W("推敲"), W("校正")]),
        N("ジャンル別文章", "応用", "説明文・レポート・物語などで異なる作法。", [W("レポート"), W("エッセイ")]),
        N("タイトルと見出し", "応用", "読む理由を作る短い言葉の工夫。", [W("見出し")]),
        N("書き続ける習慣", "実践", "量を書いて直す循環を生活に入れる。", [W("日記")]),
    ],
})


# ---------------------------------------------------------------------------
# マップ構築
# ---------------------------------------------------------------------------
def build_map(topic):
    """テーマ名からマップ dict を返す。未登録なら汎用テンプレート。"""
    if topic in KB:
        nodes = []
        for i, n in enumerate(KB[topic]):
            nodes.append({
                "id": "n%d" % i, "title": n["title"], "stage": n["stage"],
                "desc": n["desc"],
                "links": [(label, url) for label, url in n["links"]],
            })
        edges = [("n%d" % i, "n%d" % (i + 1)) for i in range(len(nodes) - 1)]
        return {"topic": topic, "generic": False, "nodes": nodes, "edges": edges}
    # 汎用テンプレート（5段階）
    steps = [
        ("入門・全体像", "前提", "「%s」とは何か、全体像と学ぶ目的を把握する。" % topic),
        ("基本用語と基礎概念", "基礎", "頻出する用語と土台になる概念を押さえる。"),
        ("仕組みと核心", "核心", "中心となる仕組みや理論を、例を通して理解する。"),
        ("応用と事例", "応用", "実際の使われ方や代表的な事例に触れて理解を深める。"),
        ("実践とアウトプット", "実践", "手を動かしたり、人に説明したりして定着させる。"),
    ]
    nodes = []
    for i, (title, stage, desc) in enumerate(steps):
        q = quote(topic)
        nodes.append({
            "id": "n%d" % i, "title": title, "stage": stage, "desc": desc,
            "links": [
                ("Wikipediaで「%s」を調べる" % topic, WIKI + "Special:Search?search=" + q),
                ("Wikipedia「%s」" % topic, WIKI + topic),
            ],
        })
    edges = [("n%d" % i, "n%d" % (i + 1)) for i in range(len(nodes) - 1)]
    return {"topic": topic, "generic": True, "nodes": nodes, "edges": edges}


def layout(m):
    """段階を列にした座標を計算し、SVG 用の描画情報を付ける。"""
    by_stage = {}
    for n in m["nodes"]:
        by_stage.setdefault(STAGES.index(n["stage"]), []).append(n)
    max_rows = max(len(v) for v in by_stage.values())
    col_w, row_h, pad_x, pad_y = 196, 86, 108, 66
    width = pad_x * 2 + col_w * (len(STAGES) - 1)
    height = pad_y * 2 + row_h * (max_rows - 1) + 30
    pos = {}
    for si, nodes in by_stage.items():
        for ri, n in enumerate(nodes):
            pos[n["id"]] = (pad_x + col_w * si, pad_y + row_h * ri, n)
    return {"width": width, "height": height, "pos": pos}


# ---------------------------------------------------------------------------
# 画面テンプレート
# ---------------------------------------------------------------------------
CSS = """
:root{
  --bg:#f7f5f0; --panel:#ffffff; --text:#26303a; --sub:#5d6b78;
  --line:#d8d2c4; --accent:#2e7d6b; --accent2:#e8f2ee;
  --node:#ffffff; --node-line:#9db8ae; --done:#cfe6da;
}
html[data-theme="dark"]{
  --bg:#161a1e; --panel:#20262c; --text:#e8ecef; --sub:#9fb0bd;
  --line:#39434c; --accent:#5cc2a7; --accent2:#24382f;
  --node:#262e36; --node-line:#4d6a5f; --done:#2f5443;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;line-height:1.7}
.wrap{max-width:1060px;margin:0 auto;padding:20px 16px 48px}
header.site{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
h1{font-size:1.5rem;margin:.2em 0}
h1 a{color:inherit;text-decoration:none}
button.theme{background:var(--panel);color:var(--text);border:1px solid var(--line);
  border-radius:999px;padding:6px 14px;cursor:pointer}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
form.search{display:flex;gap:8px;flex-wrap:wrap}
form.search input{flex:1 1 220px;padding:10px 12px;border:1px solid var(--line);
  border-radius:8px;background:var(--bg);color:var(--text);font-size:1rem}
form.search button{background:var(--accent);color:#fff;border:0;border-radius:8px;
  padding:10px 18px;font-size:1rem;cursor:pointer}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.chips a{background:var(--accent2);color:var(--text);text-decoration:none;
  border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:.9rem}
.note{color:var(--sub);font-size:.92rem}
.generic-badge{background:#fdf0d5;color:#6b5410;border:1px solid #e3cd8a;border-radius:8px;
  padding:10px 14px;margin:12px 0}
html[data-theme="dark"] .generic-badge{background:#3a3319;color:#ecd9a0;border-color:#6d5f27}
svg.map{width:100%;height:auto;display:block}
svg.map .edge{stroke:var(--node-line);stroke-width:2}
svg.map .nodebox{fill:var(--node);stroke:var(--node-line);stroke-width:1.5}
svg.map g.learned .nodebox{fill:var(--done)}
svg.map text{fill:var(--text);font-size:13px}
svg.map .stage{fill:var(--sub);font-size:13px;font-weight:bold}
.detail h2{margin:.2em 0}
.detail .stage-tag{display:inline-block;background:var(--accent2);border-radius:999px;
  padding:1px 10px;font-size:.85rem;margin-bottom:6px}
ul.links li{margin:2px 0}
a{color:var(--accent)}
table.nodes{width:100%;border-collapse:collapse}
table.nodes td,table.nodes th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
footer{color:var(--sub);font-size:.85rem;margin-top:28px}
"""

BASE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} - learnmap</title>
<style>{{ css }}</style>
<script>
(function(){var t=localStorage.getItem('learnmap-theme');
if(t){document.documentElement.setAttribute('data-theme',t);}
else if(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches){
document.documentElement.setAttribute('data-theme','dark');}})();
function toggleTheme(){var h=document.documentElement;
var next=h.getAttribute('data-theme')==='dark'?'light':'dark';
h.setAttribute('data-theme',next);localStorage.setItem('learnmap-theme',next);}
</script>
</head>
<body>
<div class="wrap">
<header class="site">
  <h1><a href="/">learnmap</a></h1>
  <button class="theme" type="button" onclick="toggleTheme()">ライト／ダーク切替</button>
</header>
{{ body|safe }}
<footer>learnmap - テーマから学びの地図をひらく小さな道具</footer>
</div>
</body>
</html>"""

HOME_BODY = """
<div class="panel">
  <p>学びたいテーマを入力すると、そのテーマを学ぶための<strong>知識マップ</strong>（前提→基礎→核心→応用→実践のつながり）を表示します。</p>
  <form class="search" action="/go" method="get">
    <input type="text" name="q" placeholder="例：Python、統計学、写真…" required>
    <button type="submit">マップを開く</button>
  </form>
  <p class="note">収録テーマ（{{ topics|length }}件）から選ぶこともできます。未収録のテーマは汎用マップで表示されます。</p>
  <div class="chips">
    {% for t in topics %}<a href="/map/{{ t }}">{{ t }}</a>{% endfor %}
  </div>
</div>
"""

MAP_BODY = """
<p><a href="/">← テーマ一覧へ</a></p>
<h1 style="font-size:1.35rem">{{ m.topic }} の学習マップ</h1>
{% if m.generic %}
<div class="generic-badge">これは<strong>登録外テーマ向けの汎用マップ</strong>です（内蔵知識ベースに「{{ m.topic }}」がないため、一般的な5段階の流れで生成しています）。</div>
{% endif %}
<div class="panel">
<svg class="map" viewBox="0 0 {{ lay.width }} {{ lay.height }}" role="img" aria-label="{{ m.topic }}の学習マップ">
  {% for si, label in stages %}
  <text class="stage" x="{{ 108 + 196 * si }}" y="30" text-anchor="middle">{{ label }}</text>
  {% endfor %}
  {% for a, b in m.edges %}
  <line class="edge" x1="{{ lay.pos[a][0] }}" y1="{{ lay.pos[a][1] }}" x2="{{ lay.pos[b][0] }}" y2="{{ lay.pos[b][1] }}" />
  {% endfor %}
  {% for n in m.nodes %}
  {% set x, y = lay.pos[n.id][0], lay.pos[n.id][1] %}
  <g id="svg-{{ n.id }}">
    <a href="/map/{{ m.topic }}?node={{ n.id }}">
      <rect class="nodebox" x="{{ x - 86 }}" y="{{ y - 25 }}" width="172" height="50" rx="9" />
      <text x="{{ x }}" y="{{ y + 5 }}" text-anchor="middle">{{ n.title }}</text>
    </a>
  </g>
  {% endfor %}
</svg>
<p class="note">ノードをクリックすると詳細が表示されます。学習済みチェックはこのブラウザに保存されます。</p>
</div>

{% if sel %}
<div class="panel detail" id="detail">
  <span class="stage-tag">段階：{{ sel.stage }}</span>
  <h2>{{ sel.title }}</h2>
  <p>{{ sel.desc }}</p>
  <h3>学習リソース</h3>
  <ul class="links">
    {% for label, url in sel.links %}<li><a href="{{ url }}" target="_blank" rel="noopener">{{ label }}</a></li>{% endfor %}
  </ul>
  <p><label><input type="checkbox" class="learned-check" data-node="{{ sel.id }}"> 学習済みにする</label></p>
</div>
{% endif %}

<div class="panel">
  <h2 style="font-size:1.1rem;margin-top:0">ノード一覧</h2>
  <table class="nodes">
    <tr><th>段階</th><th>ノード</th><th>学習済み</th></tr>
    {% for n in m.nodes %}
    <tr>
      <td>{{ n.stage }}</td>
      <td><a href="/map/{{ m.topic }}?node={{ n.id }}">{{ n.title }}</a></td>
      <td><input type="checkbox" class="learned-check" data-node="{{ n.id }}"></td>
    </tr>
    {% endfor %}
  </table>
</div>

<script>
(function(){
  var topic = {{ m.topic|tojson }};
  function key(id){ return 'learnmap:done:' + topic + ':' + id; }
  function refresh(){
    document.querySelectorAll('.learned-check').forEach(function(cb){
      var on = localStorage.getItem(key(cb.dataset.node)) === '1';
      cb.checked = on;
      var g = document.getElementById('svg-' + cb.dataset.node);
      if(g){ g.classList.toggle('learned', on); }
    });
  }
  document.querySelectorAll('.learned-check').forEach(function(cb){
    cb.addEventListener('change', function(){
      if(cb.checked){ localStorage.setItem(key(cb.dataset.node), '1'); }
      else { localStorage.removeItem(key(cb.dataset.node)); }
      refresh();
    });
  });
  refresh();
})();
</script>
"""


@app.route("/")
def index():
    body = render_template_string(HOME_BODY, topics=list(KB.keys()))
    return render_template_string(BASE, title="トップ", css=CSS, body=body)


@app.route("/go")
def go():
    q = (request.args.get("q") or "").strip()
    if not q:
        return redirect(url_for("index"))
    return redirect(url_for("show_map", topic=q))


@app.route("/map/<path:topic>")
def show_map(topic):
    topic = topic.strip()
    if not topic:
        abort(404)
    m = build_map(topic)
    lay = layout(m)
    sel = None
    node_id = request.args.get("node")
    if node_id:
        for n in m["nodes"]:
            if n["id"] == node_id:
                sel = n
                break
    body = render_template_string(
        MAP_BODY, m=m, lay=lay, sel=sel, stages=list(enumerate(STAGES)))
    return render_template_string(BASE, title=topic, css=CSS, body=body)


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

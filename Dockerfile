# ----------------------------------------------------
# ステージ 1: ビルドステージ (node:20-alpine を使用)
# ----------------------------------------------------
FROM node:20-alpine AS build

# アプリケーションの作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
# これは依存関係のインストールをキャッシュするために重要です
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# アプリケーションのソースコードを全てコピー
COPY . .

# アプリケーションをビルド
# (注: ここはプロジェクトの実際のビルドコマンドに合わせて調整が必要です。
# 例: Create React Appなら 'npm run build', Viteなら 'npm run build')
RUN npm run build


# ----------------------------------------------------
# ステージ 2: プロダクションステージ (nginx:alpine を使用)
# ----------------------------------------------------
FROM nginx:alpine AS production

# ビルドステージで作成された静的ファイルをNginxのデフォルトのWebルートにコピー
# (注: ビルド出力ディレクトリはプロジェクトのビルド設定に依存します。
# 通常は 'build'、'dist'、または '.next/static' などです)
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx設定ファイル（もしあれば）をコピー
# COPY nginx.conf /etc/nginx/nginx.conf

# コンテナがリッスンするポートを公開
EXPOSE 80

# Nginxをフォアグラウンドで実行
CMD ["nginx", "-g", "daemon off;"]

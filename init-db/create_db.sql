-- init-db/create_db.sql

-- データベースが存在しない場合のみ作成する
SELECT 'CREATE DATABASE minecraft_movie_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'minecraft_movie_db')\gexec

-- 作成したデータベースに接続し、スキーマ定義を実行する場合
-- \c minecraft_movie_db;
-- \i /docker-entrypoint-initdb.d/schema.sql; -- この行はDockerが自動でやってくれるため不要
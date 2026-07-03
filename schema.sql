DROP TABLE IF EXISTS "Photos_has_Tags" CASCADE;
DROP TABLE IF EXISTS "Users_has_Users" CASCADE;
DROP TABLE IF EXISTS "Likes"           CASCADE;
DROP TABLE IF EXISTS "Comments"        CASCADE;
DROP TABLE IF EXISTS "Tags"            CASCADE;
DROP TABLE IF EXISTS "Photos"          CASCADE;
DROP TABLE IF EXISTS "Albums"          CASCADE;
DROP TABLE IF EXISTS "Users"           CASCADE;

CREATE TABLE "Users" (
  "User-id"  VARCHAR(20) PRIMARY KEY,
  "Name"     VARCHAR(45) NOT NULL,
  "Surname"  VARCHAR(45) NOT NULL,
  "Email"    VARCHAR(45) NOT NULL UNIQUE,
  "DOB"      DATE        NULL,
  "Origin"   VARCHAR(45) NULL,
  "Sex"      VARCHAR(45) NOT NULL,
  "Password" VARCHAR(45) NOT NULL,
  "Data"     BYTEA       NULL
);

CREATE TABLE "Albums" (
  "Album-id"      SERIAL PRIMARY KEY,
  "User-id"       VARCHAR(20) NOT NULL,
  "Title"         VARCHAR(45) NOT NULL,
  "Creation_date" DATE        NOT NULL,
  CONSTRAINT "Unique_album_per_user" UNIQUE ("User-id", "Title"),
  CONSTRAINT "FK_Albums_Users" FOREIGN KEY ("User-id") REFERENCES "Users" ("User-id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "Photos" (
  "Photo-id" SERIAL PRIMARY KEY,
  "Data"     BYTEA       NOT NULL,
  "Caption"  TEXT        NOT NULL,
  "Album-id" INTEGER NOT NULL,
  CONSTRAINT "FK_Photos_Albums" FOREIGN KEY ("Album-id") REFERENCES "Albums" ("Album-id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "Tags" (
  "Title" TEXT NOT NULL,
  PRIMARY KEY ("Title"),
  CONSTRAINT "Tag_lowercase_no_spaces" CHECK ("Title" = lower("Title") AND "Title" !~ '\s')
);

CREATE TABLE "Likes" (
  "User-id"  VARCHAR(20) NOT NULL,
  "Photo-id" INTEGER NOT NULL,
  PRIMARY KEY ("User-id", "Photo-id"),
  CONSTRAINT "FK_Likes_Users" FOREIGN KEY ("User-id") REFERENCES "Users" ("User-id") ON DELETE CASCADE,
  CONSTRAINT "FK_Likes_Photos" FOREIGN KEY ("Photo-id") REFERENCES "Photos" ("Photo-id") ON DELETE CASCADE
);

CREATE TABLE "Comments" (
  "Comment-id"   SERIAL PRIMARY KEY,
  "Photo-id"     INTEGER NOT NULL,
  "User-id"      VARCHAR(20) NULL,
  "Comment_text" TEXT        NOT NULL,
  "Post_date"    DATE        NOT NULL,
  CONSTRAINT "FK_Comments_Photos" FOREIGN KEY ("Photo-id") REFERENCES "Photos" ("Photo-id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "FK_Comments_Users" FOREIGN KEY ("User-id") REFERENCES "Users" ("User-id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE "Users_has_Users" (
  "User_1" VARCHAR(20) NOT NULL,
  "User_2" VARCHAR(20) NOT NULL,
  PRIMARY KEY ("User_1", "User_2"),
  CONSTRAINT "No_self_friend" CHECK ("User_1" <> "User_2"),
  CONSTRAINT "FK_Users_has_Users_Users1" FOREIGN KEY ("User_1") REFERENCES "Users" ("User-id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "FK_Users_has_Users_Users2" FOREIGN KEY ("User_2") REFERENCES "Users" ("User-id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "Photos_has_Tags" (
  "Photo-id" INTEGER NOT NULL,
  "Title"    TEXT        NOT NULL,
  PRIMARY KEY ("Photo-id", "Title"),
  CONSTRAINT "FK_Photos_has_Tags_Photos" FOREIGN KEY ("Photo-id") REFERENCES "Photos" ("Photo-id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "FK_Photos_has_Tags_Tags" FOREIGN KEY ("Title") REFERENCES "Tags" ("Title") ON DELETE CASCADE ON UPDATE CASCADE
);
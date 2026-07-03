BEGIN;


TRUNCATE TABLE "Users" CASCADE;
TRUNCATE TABLE "Tags" CASCADE;


INSERT INTO "Users" ("User-id", "Name", "Surname", "Email", "Sex", "Password")
VALUES
('user_A', 'Anna', 'Pappa', 'anna@test.com', 'F', '1234'),
('user_B', 'Vasilis', 'Lykos', 'vasilis@test.com', 'M', '1234'),
('user_C', 'Giorgos', 'Fotas', 'giorgos@test.com', 'M', '1234')
ON CONFLICT DO NOTHING;
INSERT INTO "Users_has_Users" ("User_1", "User_2")
VALUES

('user_A', 'user_B'),
('user_B', 'user_A'),


('user_B', 'user_C'),
('user_C', 'user_B')
ON CONFLICT DO NOTHING;

COMMIT;

BEGIN;

-- Καθαρισμός πινάκων για να περαστούν τα δεδομένα από την αρχή
TRUNCATE TABLE "Users" CASCADE;
TRUNCATE TABLE "Tags" CASCADE;

-- 1. Εισαγωγή Χρηστών
INSERT INTO "Users" ("User-id", "Name", "Surname", "Email", "Sex", "Password") VALUES
('user_A', 'Anna', 'Pappa', 'anna@test.com', 'Female', '1234'),
('user_B', 'Vasilis', 'Lykos', 'vasilis@test.com', 'Male', '1234'),
('user_C', 'Giorgos', 'Fotas', 'giorgos@test.com', 'Male', '1234')
ON CONFLICT DO NOTHING;

-- 2. Εισαγωγή Φιλιών
INSERT INTO "Users_has_Users" ("User_1", "User_2") VALUES
('user_A', 'user_B'),
('user_B', 'user_A'),
('user_B', 'user_C'),
('user_C', 'user_B')
ON CONFLICT DO NOTHING;

-- 3. Εισαγωγή Άλμπουμ (Ημερομηνίες δημιουργίας)
INSERT INTO "Albums" ("User-id", "Title", "Creation_date") VALUES
('user_A', 'Φύση & Τοπία', '2026-06-01'),
('user_B', 'Αστικά Τοπία', '2026-06-02'),
('user_C', 'Αθλητισμός', '2026-06-03');

-- 4. Εισαγωγή Φωτογραφιών (Διαβάζει τα τοπικά αρχεία)
INSERT INTO "Photos" ("Data", "Caption", "Album-id") VALUES
(pg_read_binary_file('/Users/jeryg/Desktop/K29-Delis/GalanosGerasimos-Prj3-S26/GerasimosGalanos+AthanasiosZafeiris-Proj3/photos/nature1.jpg'), 'Μαγευτικό τοπίο στο βουνό', (SELECT "Album-id" FROM "Albums" WHERE "Title" = 'Φύση & Τοπία' AND "User-id" = 'user_A')),
(pg_read_binary_file('/Users/jeryg/Desktop/K29-Delis/GalanosGerasimos-Prj3-S26/GerasimosGalanos+AthanasiosZafeiris-Proj3/photos/city1.jpg'), 'Βόλτα στην πόλη', (SELECT "Album-id" FROM "Albums" WHERE "Title" = 'Αστικά Τοπία' AND "User-id" = 'user_B')),
(pg_read_binary_file('/Users/jeryg/Desktop/K29-Delis/GalanosGerasimos-Prj3-S26/GerasimosGalanos+AthanasiosZafeiris-Proj3/photos/sports1.jpg'), 'Η στιγμή της δράσης', (SELECT "Album-id" FROM "Albums" WHERE "Title" = 'Αθλητισμός' AND "User-id" = 'user_C'));

-- 5. Εισαγωγή Ετικετών (Tags)
INSERT INTO "Tags" ("Title") VALUES
('nature'), ('beautiful'), ('mountains'),
('city'), ('urban'), ('street'),
('sports'), ('action'), ('football');

-- 6. Αντιστοίχιση Ετικετών στις Φωτογραφίες
INSERT INTO "Photos_has_Tags" ("Photo-id", "Title") VALUES
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό'), 'nature'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό'), 'beautiful'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό'), 'mountains'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Βόλτα στην πόλη'), 'city'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Βόλτα στην πόλη'), 'urban'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Βόλτα στην πόλη'), 'street'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Η στιγμή της δράσης'), 'sports'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Η στιγμή της δράσης'), 'action'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Η στιγμή της δράσης'), 'football');

-- 7. Εισαγωγή Σχολίων (Από άλλους χρήστες)
INSERT INTO "Comments" ("Photo-id", "User-id", "Comment_text", "Post_date") VALUES
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό'), 'user_B', 'Απίστευτη λήψη!', '2026-06-03'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό'), 'user_C', 'Πανέμορφο μέρος.', '2026-06-03'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Βόλτα στην πόλη'), 'user_A', 'Ποια οδός είναι αυτή;', '2026-06-03'),
((SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Η στιγμή της δράσης'), 'user_A', 'Φοβερός συγχρονισμός!', '2026-06-03');

-- 8. Εισαγωγή Likes
INSERT INTO "Likes" ("User-id", "Photo-id") VALUES
('user_B', (SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό')),
('user_C', (SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Μαγευτικό τοπίο στο βουνό')),
('user_A', (SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Βόλτα στην πόλη')),
('user_A', (SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Η στιγμή της δράσης')),
('user_B', (SELECT "Photo-id" FROM "Photos" WHERE "Caption" = 'Η στιγμή της δράσης'));

COMMIT;
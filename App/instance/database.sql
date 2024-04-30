CREATE TABLE IF NOT EXISTS product (
   id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite uses INTEGER for auto-increment
   name TEXT NOT NULL,
   price REAL NOT NULL,                   -- REAL in SQLite corresponds to DECIMAL in other SQL databases
   category TEXT NOT NULL,
   image_filename TEXT NOT NULL
);

CREATE TABLE "product_images" (
    "id" INTEGER,
    "product_id" INTEGER NOT NULL,
    "filename" TEXT NOT NULL,
    "color" TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
);

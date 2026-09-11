-- Chinook-style music store. Explicit IDs so SQLite and Postgres stay in sync.
DROP TABLE IF EXISTS invoice_lines;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS tracks;
DROP TABLE IF EXISTS albums;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS artists;

CREATE TABLE artists (
    artist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE albums (
    album_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id INTEGER NOT NULL REFERENCES artists (artist_id)
);

CREATE TABLE tracks (
    track_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    album_id INTEGER NOT NULL REFERENCES albums (album_id),
    genre_id INTEGER NOT NULL REFERENCES genres (genre_id),
    milliseconds INTEGER NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL,
    reports_to INTEGER REFERENCES employees (employee_id),
    city TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    email TEXT NOT NULL,
    support_rep_id INTEGER NOT NULL REFERENCES employees (employee_id)
);

CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    invoice_date TEXT NOT NULL,
    billing_country TEXT NOT NULL,
    total REAL NOT NULL
);

CREATE TABLE invoice_lines (
    invoice_line_id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices (invoice_id),
    track_id INTEGER NOT NULL REFERENCES tracks (track_id),
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL
);

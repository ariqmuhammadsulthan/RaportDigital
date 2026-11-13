CREATE TABLE IF NOT EXISTS users(name TEXT PRIMARY KEY, password TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, name TEXT NOT NULL, csrf TEXT NOT NULL,
    seen INTEGER NOT NULL, created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempts(ip TEXT PRIMARY KEY, start INTEGER NOT NULL, count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS books(owner TEXT, program TEXT, year INTEGER, rev INTEGER, data BLOB,
    PRIMARY KEY(owner,program,year));
CREATE TABLE IF NOT EXISTS issues(id INTEGER PRIMARY KEY, owner TEXT, program TEXT, year INTEGER,
    rev INTEGER, grade TEXT, semester TEXT, issued INTEGER, data BLOB,
    UNIQUE(owner,program,year,rev,grade,semester));
CREATE TABLE IF NOT EXISTS drafts(owner TEXT, program TEXT, year INTEGER, rev INTEGER, data BLOB,
    PRIMARY KEY(owner,program,year,rev));
CREATE TRIGGER IF NOT EXISTS keep_issued BEFORE UPDATE ON issues
BEGIN SELECT RAISE(ABORT,'issued record'); END;
CREATE TRIGGER IF NOT EXISTS retain_issued BEFORE DELETE ON issues
BEGIN SELECT RAISE(ABORT,'issued record'); END;

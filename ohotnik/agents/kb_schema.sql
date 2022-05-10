/*
  SQL_KnowledgeBase database creation

  - Variables    : An object in the KB
  - Properties_1 : An instantiated predicate for variables in the KB, arity 1
  - Properties_2 : ... arity 2
  - Predicates   : Predicate templates
  - Aliases      : Alias of a predicate which should be True for only one input
  - Rules        : Rules defining the outcome of actions on variables in
                   the KB
*/

/* Create Variables table
*/

CREATE TABLE IF NOT EXISTS Variables (
    KBName          TEXT PRIMARY KEY,
    ParserName      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Properties_1 (
    Prop_ID         INTEGER PRIMARY KEY AUTOINCREMENT,
    Predicate       TEXT NOT NULL,
    Arg0            TEXT NOT NULL,
    Value           BOOLEAN
);

CREATE TABLE IF NOT EXISTS Predicates (
    Name            TEXT PRIMARY KEY,
    Arity           TINYINT UNSIGNED,
    Implicit        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS Functions (
    Name            TEXT PRIMARY KEY,
    Predicate       TEXT,
    Argument        TINYINT UNSIGNED
);

CREATE TABLE IF NOT EXISTS Rules (
    Name            TEXT PRIMARY KEY,
    Arity           TINYINT UNSIGNED,
    Preconditions   TEXT,
    Postconditions  TEXT
);


/* Create Postcondition link table
   One entry for each arity-1 predicate applied to a variable which is
   affected by a rule
*/
CREATE TABLE IF NOT EXISTS Postcondition_Link (
    Plink_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Rule            TEXT NOT NULL,
    Predicate       TEXT NOT NULL
);

/* Create Precondition link table
   One entry for each arity-1 predicate applied to a variable as a
   precondition for a rule
*/
CREATE TABLE IF NOT EXISTS Precondition_Link (
    Plink_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Rule            TEXT NOT NULL,
    Predicate       TEXT NOT NULL
);

-- This is a sqlite3 DB schema, defined using type aliases in case you
-- migrate to a stricter RDBMS.

-- Note: Foreign keys are not checked in sqlite unless you set
--       PRAGMA foreign_keys = ON 
--       for every connection!

CREATE TABLE proposals (
    id INTEGER PRIMARY KEY,
    title TEXT,
    file_number INTEGER UNIQUE,
    status VARCHAR(255),
    introduction_date TEXT, -- Note: DATE would have NUMERIC affinity
    proposal_type VARCHAR(255)
);

CREATE TABLE vote_events (
    id INTEGER PRIMARY KEY,
    vote_date TEXT, -- Note: DATE would have NUMERIC affinity
    proposal_id INTEGER REFERENCES proposals(id)
);

CREATE TABLE legislators (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE
);

CREATE TABLE votes (
    legislator_id INTEGER REFERENCES legislators(id),
    vote_event_id INTEGER REFERENCES vote_events(id),
    aye_vote BOOLEAN, -- 1 => aye, 0 => nay
    -- Note: If a legislator does not vote on a proposal, there will be no 
     --      entry in this table.

    PRIMARY KEY (legislator_id, vote_event_id)
);

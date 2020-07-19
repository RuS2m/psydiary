CREATE TABLE rates (
    chat_id BIGINT,
    date_time DATE,
    rate    BIGINT,
    PRIMARY KEY(chat_id, date_time)
);
CREATE TABLE diary (
    chat_id BIGINT,
    date_time   TIMESTAMP WITH TIME ZONE,
    a1  TEXT,
    b1  TEXT,
    c1  TEXT,
    a2  TEXT,
    b2  TEXT,
    c2  TEXT,
    PRIMARY KEY(chat_id, date_time)
);
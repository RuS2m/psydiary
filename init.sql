CREATE TABLE rates (
    chat_id BIGINT,
    date_time DATE,
    rate    BIGINT,
    PRIMARY KEY(chat_id, date_time)
);
CREATE TABLE diary (
    note_id BIGINT,
    chat_id BIGINT,
    date_time   TIMESTAMP WITH TIME ZONE,
    a  TEXT,
    b  TEXT,
    c  TEXT,
    b1  TEXT,
    c1  TEXT,
    is_reflected    BOOLEAN,
    PRIMARY KEY(note_id, chat_id, date_time)
);
CREATE TABLE answer_needs (
    chat_id BIGINT,
    is_answer_needed    BOOLEAN,
    answer_type TEXT,
    additional_info TEXT
);
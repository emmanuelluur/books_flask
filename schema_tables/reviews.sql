-- Create the table in the specified schema
CREATE TABLE tbl_reviews
(
    review_id SERIAL PRIMARY KEY, -- primary key column
    book_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rate INTEGER,
    review TEXT,
    -- specify  FOREIGN KEYS
    FOREIGN KEY (book_id) REFERENCES tbl_books (book_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES tbl_user (user_id) ON DELETE CASCADE
);
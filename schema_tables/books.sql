
-- Create the table in the specified schema
CREATE TABLE tbl_books
(
    book_id SERIAL PRIMARY KEY, -- primary key column
    isbn varchar(60), 
    title varchar(60),
    author varchar(60),
    year_book varchar(60)
    -- specify more columns here
);

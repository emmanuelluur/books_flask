
-- Create the table in the specified schema
CREATE TABLE tbl_user
(
    user_id SERIAL PRIMARY KEY, -- primary key column
    name varchar(60),
    username varchar(60), 
    password text
    -- specify more columns here
);

import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine("URI")
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO tbl_books (isbn,title,author,year_book) values (:isbn,:title,:author,:year)",
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"book {title} added")
    db.commit()

if __name__ == "__main__":
    main()
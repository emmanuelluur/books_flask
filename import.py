import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine("postgres://gacveuwncytnzj:920f184b5eb0a76b5dd2a590413d863f72f27a5a659e139f1400193d4ce4e70a@ec2-50-19-221-38.compute-1.amazonaws.com:5432/dan9e2fm3hevo2")
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
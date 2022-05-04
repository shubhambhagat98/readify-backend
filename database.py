
import pymysql


class Database:

    def __init__(self):

        host = "us-cdbr-east-04.cleardb.com"
        user = "b57d4729a12867"
        password = "388430bc"
        db = 'heroku_eebc78f02376aa6'

        # host = "127.0.0.1"
        # user = "root"
        # password = "rootroot"
        # db = 'readify'
        self.con = pymysql.connect(
            host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    def getBooks(self):
        result = self.cur.execute(
            "SELECT book_id, book_author, book_genre, book_image, book_like_percent, book_rating, book_score, book_title, book_votes FROM readify_book limit 20000")
        return result

    def getBookData(self, book_id):
        result = self.cur.execute(
            "SELECT book_id, book_author, book_genre, book_description, book_image, book_like_percent, book_rating, book_score, book_title, book_votes FROM readify_book WHERE book_id = %s", (book_id))
        return result

    def getBooklist(self, user_id):
        result = self.cur.execute(
            "SELECT booklist_id, booklist_name FROM readify_booklist where user_id = %s", (user_id))
        return result

    def getBooklistWithData(self, user_id):
        result = self.cur.execute(
            "SELECT booklist_id, booklist_name FROM readify_booklist where user_id = %s", (user_id))
        if result == 0:
            return []
        booklists = self.cur.fetchall()
        for idx, booklist in enumerate(booklists):
            allbooksinbooklist = []
            self.cur.execute(
                "SELECT b.book_id, b.book_image, b.book_rating, b.book_title FROM readify_book b,readify_booklist_data bl WHERE b.book_id = bl.book_id AND bl.booklist_id = %s ", (booklist["booklist_id"]))
            ans = self.cur.fetchall()
            allbooksinbooklist.insert(0, ans)
            if len(allbooksinbooklist) > 0:
                booklist["books"] = allbooksinbooklist[0]
                booklists[idx] = booklist
            else:
                booklist["books"] = []
                booklists[idx] = booklist

        return booklists

    def createBooklist(self, user_id, booklist_name):
        result = self.cur.execute(
            "INSERT INTO readify_booklist(booklist_name, user_id) VALUES (%s, %s)", (booklist_name, user_id))
        return result

    def createBooklistWithBook(self, user_id, booklist_name, book_id):
        result = self.cur.execute(
            "INSERT INTO readify_booklist(booklist_name, user_id) VALUES (%s, %s)", (booklist_name, user_id))
        book_list = self.getBooklistId(booklist_name, user_id)
        print(book_list)
        result1 = self.cur.execute(
            "INSERT INTO readify_booklist_data(booklist_id, book_id) VALUES (%s, %s)", (book_list[0]["booklist_id"], book_id))
        return result + result1

    def deleteFromBooklist(self, booklist_id, book_id):
        result = self.cur.execute(
            "DELETE FROM readify_booklist_data WHERE booklist_id = %s AND book_id = %s", (booklist_id, book_id))
        return result

    def deleteBooklist(self, user_id, booklist_id):
        result = self.cur.execute(
            "DELETE FROM readify_booklist_data WHERE booklist_id = %s", (booklist_id))
        result1 = self.cur.execute(
            "DELETE FROM readify_booklist WHERE booklist_id = %s AND user_id = %s", (booklist_id, user_id))
        return result + result1

    def getBooklistId(self, booklist_name, user_id):
        self.cur.execute(
            "SELECT readify_booklist_id FROM booklist WHERE user_id = %s AND booklist_name = %s", (user_id, booklist_name))
        result = self.cur.fetchall()
        return result

    def insertInBooklist(self, booklist_id, book_id):
        result = self.cur.execute(
            "SELECT * FROM readify_booklist_data WHERE booklist_id = %s AND book_id = %s", (booklist_id, book_id))
        if result == 0:
            result1 = self.cur.execute(
                "INSERT INTO readify_booklist_data(booklist_id, book_id) VALUES (%s, %s)", (booklist_id, book_id))
            return result1
        return 2

    def updateBooklistName(self, user_id, booklist_id, booklist_name):
        result = self.cur.execute(
            "UPDATE readify_booklist SET booklist_name = %s WHERE user_id = %s AND booklist_id = %s", (booklist_name, user_id, booklist_id))
        return result

    def createUsers(self, first_name, last_name, email_id, password, genre_1, genre_2, genre_3):
        self.cur.execute(
            "INSERT INTO readify_user(first_name, last_name, email_id, password, genre_1, genre_2, genre_3) VALUES (%s, %s, %s, %s, %s, %s, %s)", (first_name, last_name, email_id, password, genre_1, genre_2, genre_3))
        result = self.cur.execute(
            "SELECT user_id FROM readify_user WHERE first_name = %s AND last_name = %s AND email_id = %s", (first_name, last_name, email_id))
        return result

    def getProfile(self, user_id):
        result = self.cur.execute(
            "SELECT first_name, last_name, email_id, genre_1, genre_2, genre_3 FROM readify_user WHERE user_id = %s", (user_id))
        return result

    def getUser(self, email_id):
        result = self.cur.execute(
            "SELECT user_id, first_name, last_name, password FROM readify_user where email_id = %s", (email_id))
        return result

    def getBookGenreCount(self):
        result = self.cur.execute(
            "SELECT COUNT(TRIM(both ' ' from book_genre)) AS count, book_genre FROM readify_genre GROUP BY book_genre ORDER BY count DESC LIMIT 10")
        return result

    def getGenreAvgRatingCount(self):
        result = self.cur.execute(
            "SELECT AVG(book_rating), genre from (SELECT book_title, book_rating, TRIM(both ' ' from g.book_genre) AS genre FROM readify_book b, readify_genre g WHERE b.book_id = g.book_id) AS semi GROUP BY genre")
        return result

    def closeCursor(self):
        self.cur.close()
        self.con.close()

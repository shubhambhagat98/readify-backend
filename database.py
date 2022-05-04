

import pymysql
import random
import recommendation

import yaml

db = yaml.safe_load(open('db.yaml'))
host = db["host"]
user = db["user"]
password = db["password"]
db = db["db"]

class Database:



    def __init__(self):
        self.con = pymysql.connect(
            host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    def getBooks(self):
        result = self.cur.execute(
            "SELECT book_id, book_author, book_genre, book_image, book_like_percent, book_rating, book_score, book_title, book_votes FROM readify_book limit 20000")
        return result
    
    def getBooksWithCount(self, keyword, rating, min_lp, max_lp, order, page, get_new_count):
        result = ""
        query1 = "SELECT book_id, book_image, book_rating, book_title FROM readify_book"
        query2 = " SELECT count(*) as page_count from readify_book "
        final_count = 0

        filter_query, param_list = self.getFilterQuery(keyword, rating, min_lp, max_lp)

        if get_new_count == "true":
            query2 += filter_query   #--------------update filter_query2 to get total count of records----------------
            # print("total count query executed")
            result = self.cur.execute(query2, param_list)
            if result > 0:
                total_count = self.cur.fetchone()
                # print("total count: ", total_count['page_count'])
                final_count = total_count['page_count']
        
        
          

        #----------------check for order----------------
        if order != "default" and order == "ascending":
            filter_query += " ORDER BY book_rating"
        elif order != "default" and order == "descending":
            filter_query += " ORDER BY book_rating DESC "

        


        filter_query += " LIMIT 30 OFFSET %s"
        offset = int((page-1)*30)
        param_list.append(offset)
        query1 += filter_query
        
        # print("page offset query executed")
        result = self.cur.execute(query1, param_list)
        book_list = []
        if result > 0 :
            book_list = self.cur.fetchall()
        # else:
        #     print(result)
        
        
        return final_count, book_list


    def getFilterQuery(self, keyword, rating, min_lp, max_lp):
        filter_query = ""
        param_list = []
        count = 0

        #----------------check for keyword----------------
        if keyword != "":
            filter_query += " WHERE (book_title like %s or book_author like %s or book_genre like %s) "
            param_list.append("%"+keyword+"%")
            param_list.append("%"+keyword+"%")
            param_list.append("%"+keyword+"%")
            count += 1
        
        #----------------check for rating----------------
        if rating > 0 and count == 0:
            filter_query += " WHERE book_rating >= %s"
            param_list.append(rating)
            count += 1
        elif rating > 0 and count > 0:
            filter_query += " and book_rating >= %s "
            param_list.append(rating)
            count += 1

        #----------------check for likepercent----------------
        if min_lp > 0 and max_lp < 100:
            if count > 0 :
                filter_query += " and (book_like_percent BETWEEEN %s and %s )"
            else: 
                filter_query += " WHERE (book_like_percent BETWEEEN %s and %s ) "
            param_list.append(min_lp)
            param_list.append(max_lp)
            count += 1
        elif min_lp == 0 and max_lp < 100:
            if count > 0 :
                filter_query += " and (book_like_percent <= %s)"
            else: 
                filter_query += " WHERE (book_like_percent <= %s) "
            param_list.append(max_lp)
            count += 1
        elif min_lp > 0 and max_lp == 100: 
            if count > 0 :
                filter_query += " and (book_like_percent >= %s)"
            else: 
                filter_query += " WHERE (book_like_percent >= %s) "
            param_list.append(min_lp)
            count += 1

        return filter_query, param_list

    def getBookData(self, book_id):
        result = self.cur.execute(
            "SELECT book_id, book_author, book_genre, book_description, book_image, book_like_percent, book_rating, book_score, book_title, book_votes FROM readify_book WHERE book_id = %s", (book_id))
        return result

    def getBooklist(self, user_id):
        result = self.cur.execute(
            "SELECT booklist_id, booklist_name FROM readify_booklist where user_id = %s", (user_id))
        return result

    def getBooklistWithData(self, user_id):
        # self.getRecommendationList(user_id)
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

    def getRecommendationList(self,user_id):
        result = self.cur.execute("SELECT booklist_id FROM readify_booklist where user_id = %s", (user_id))
        if result == 0:
            # cold start
            # print("no booklist") 
            return self.getColdStartRecommendations(user_id)
        else:
            allbooksinbooklist = []
            booklists = self.cur.fetchall()
            # print(booklists)
            for booklist in booklists:
                self.cur.execute("SELECT book_id FROM readify_booklist_data bl WHERE booklist_id = %s ", (booklist["booklist_id"]))
                ans = self.cur.fetchall()
                if len(ans) >0:
                    allbooksinbooklist+= ans
            # print("book_id for rec",allbooksinbooklist)

            if len(allbooksinbooklist) > 0:
                rec_book_id_list = recommendation.get_recommendations_list(allbooksinbooklist)
                # print(rec_book_id_list)
                # print(len(rec_book_id_list))
                
                format_string_placeholders = ','.join(['%s']*len(rec_book_id_list))
                
                self.cur.execute("SELECT book_id, book_image, book_rating, book_title FROM readify_book where book_id in (%s)"%format_string_placeholders,rec_book_id_list )
                final_rec_list = self.cur.fetchall()
                return final_rec_list, len(final_rec_list)
                
            else:
                # print("cold start")
                return self.getColdStartRecommendations(user_id)
            
    

    def getColdStartRecommendations(self, user_id):
        result = self.cur.execute("SELECT genre_1, genre_2, genre_3 from readify_user where user_id = %s", (user_id))
        genre_preference = self.cur.fetchall()
        input_genres = []
        for key in genre_preference[0].keys():
            input_genres.append(genre_preference[0][key].replace(" ","_"))
        input_genres = " ".join(input_genres)
        
        rec_book_id_list = recommendation.get_recom_cold_start([input_genres])
        # print(sorted(rec_book_id_list))
        format_string_placeholders = ','.join(['%s']*len(rec_book_id_list))
        self.cur.execute("SELECT book_id, book_image, book_rating, book_title FROM readify_book where book_id in (%s)"%format_string_placeholders,rec_book_id_list )
        final_rec_list = self.cur.fetchall()
        
        return final_rec_list, len(final_rec_list)

        


    def getBookPageRecommendations(self, book_id):
       
        rec_book_id_list = recommendation.get_recomm_for_book(book_id)
      
        format_string_placeholders = ','.join(['%s']*len(rec_book_id_list))

        self.cur.execute("SELECT book_id, book_image, book_rating, book_title, book_author FROM readify_book where book_id in (%s)"%format_string_placeholders,rec_book_id_list )
        final_rec_list = self.cur.fetchall()

        # for book in final_rec_list:
        #     print(book,"\n")

        return final_rec_list

    def fetchGenres(self):
        result = self.cur.execute("SELECT DISTINCT book_genre FROM readify_genre ")
        genre_list = self.cur.fetchall();
        final_genres = [ x['book_genre'] for x in genre_list]
        return final_genres

        

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
            "SELECT booklist_id FROM readify_booklist WHERE user_id = %s AND booklist_name = %s", (user_id, booklist_name))
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
        parameter = [booklist_name, user_id, booklist_id]
        para = tuple(parameter)
        print(para)
        result = self.cur.execute(
            "UPDATE readify_booklist SET booklist_name = %s WHERE user_id = %s AND booklist_id = %s", para)
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

    def updateProfile(self, user_id, first_name, last_name, email_id, genre_1, genre_2, genre_3):
        print("before execute query")
        result = self.cur.execute("UPDATE readify_user SET first_name = %s, last_name = %s, email_id = %s, genre_1 = %s, genre_2 = %s, genre_3 = %s WHERE user_id = %s", (
            first_name, last_name, email_id, genre_1, genre_2, genre_3, user_id))
        return result

    def bookPageRecommendations(self, book_id):
        self.cur.execute("SELECT b.book_id, b.book_title, b.book_rating, b.book_image FROM readify_book b JOIN readify_genre g ON (b.book_id = g.book_id) WHERE b.book_id != %s and b.book_author like CONCAT ('%%' , (SELECT book_author FROM readify_book WHERE book_id = %s), '%%' ) group by b.book_id, b.book_title, b.book_rating, b.book_image", (book_id, book_id))

        authordata = self.cur.fetchall()

        self.cur.execute("SELECT b.book_id, b.book_title, b.book_rating, b.book_image FROM readify_book b, readify_genre g WHERE b.book_id!= %s and g.book_genre IN (SELECT book_genre FROM readify_genre WHERE book_id = %s) AND (b.book_id = g.book_id) group by b.book_id,b.book_title, b.book_rating, b.book_image  LIMIT 28", (book_id, book_id))

        genredata = self.cur.fetchall()

        if len(authordata) >= 8:
            author = list(random.sample(authordata, 8))
        else:
            author = list(authordata)
        genre = random.sample(genredata, 18 - len(author))
        res = author + genre
        return res

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

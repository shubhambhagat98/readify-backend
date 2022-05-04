from crypt import methods
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
import database
import maketoken
import yaml

app = Flask(__name__)
CORS(app)

db = yaml.safe_load(open('db.yaml'))
app.config['SECRET_KEY'] = db['secret_key']


@app.route('/hello', methods=['POST', 'GET'])
def index():
    return {"message": "success"}


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    print("inside signup")
    mysql = database.Database()
    if request.method == "POST":
        payload = request.get_json()
        first_name = payload['firstName']
        last_name = payload['lastName']
        email_id = payload['emailId']
        password = payload['password']
        genre_1 = payload['genre1']
        genre_2 = payload['genre2']
        genre_3 = payload['genre3']
        password = generate_password_hash(password)
        result = mysql.createUsers(first_name, last_name, email_id,
                                   password, genre_1, genre_2, genre_3)
        mysql.con.commit()
        if result > 0:
            user_id = mysql.cur.fetchall()[0]['user_id']
            mysql.closeCursor()
            response = {
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'email_id': email_id
            }
            return maketoken.encode_token(app, response, user_id)
        else:
            mysql.closeCursor()
            return jsonify({
                'message': 'Invalid credentials, Try again!!'
            }), 401
    mysql.closeCursor()
    return jsonify({
        'message': 'Forbidden method !!'
    }), 403


@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        payload = request.get_json()
        email_id = payload["emailId"]
        password = payload["password"]
        mysql = database.Database()

        result = mysql.getUser(email_id)
        if result > 0:
            userDetails = mysql.cur.fetchall()
            mysql.closeCursor()

            if check_password_hash(userDetails[0]['password'], password):
                response = {
                    'user_id': userDetails[0]['user_id'],
                    'first_name': userDetails[0]['first_name'],
                    'last_name': userDetails[0]['last_name']
                }

                return maketoken.encode_token(app, response, userDetails[0]['user_id'])

            return jsonify({
                'message': 'Invalid password, Try again!!'
            }), 403

        return jsonify({
            'message': 'User not found !!'
        }), 403

@app.route('/genres', methods=['GET'])
def getGenres():
    mysql = database.Database()
    genres = mysql.fetchGenres()
    mysql.closeCursor()
    return jsonify({
                    'genres': genres
                }), 200



@app.route('/profile', methods=['GET'])
def getProfile():
    mysql = database.Database()
    if request.method == 'GET':
        user_id = request.args.get('id')
        token = request.headers['Authorization'].split(" ")[1]
        if maketoken.decode_token(app, int(user_id), token):
            result = mysql.getProfile(user_id)
            if result > 0:
                profile = mysql.cur.fetchall()
                mysql.closeCursor()
                return jsonify({"profile": profile[0], "token": token}), 200
            else:
                mysql.closeCursor()
                return jsonify({
                    'message': 'Profile not found !!'
                }), 403
        return jsonify({
            'message': 'Token is invalid !!'
        }), 401



@app.route('/updateprofile', methods=['PUT'])
def updateProfile():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    first_name = payload['firstName']
    last_name = payload['lastName']
    email_id = payload['emailId']
    genre_1 = payload['genre1']
    genre_2 = payload['genre2']
    genre_3 = payload['genre3']
    print(payload)
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        print("before update")
        result = mysql.updateProfile(
            user_id, first_name, last_name, email_id, genre_1, genre_2, genre_3)
        mysql.con.commit()
        mysql.closeCursor()
        print("result:", result)
        if result > 0:
            return jsonify({"message": "success"}), 200
    return jsonify({
        'message': 'Token is invalid !!'
    }), 401


@app.route('/books', methods = ['GET'])
def getBooks():
    mysql = database.Database()
    keyword = request.args.get('keyword')
    rating = int(request.args.get('rating'))
    min_lp = int(request.args.get('min'))
    max_lp = int(request.args.get('max'))
    order = request.args.get('order')
    page = int(request.args.get('page'))
    get_new_count = request.args.get('getnewcount')
    # print(get_new_count)
    
    # print("keyword:", keyword, "\trating:", rating, "\tmin:",min_lp, "\tmax:", max_lp, "\torder: ",order, "\tpage:",page)
         
    total_count, book_list = mysql.getBooksWithCount(keyword, rating, min_lp, max_lp, order, page, get_new_count) 
    mysql.closeCursor()
    if get_new_count == "true" :
        return jsonify({
            'total_count' : total_count,
            'books': book_list
        }), 200
    else:
        return jsonify({
            'books': book_list
        }), 200

@app.route('/bookdata', methods=['GET'])
def getBookData():
    mysql = database.Database()
    book_id = request.args.get('id')
    result = mysql.getBookData(book_id)
    mysql.closeCursor()
    if result > 0:
        book = mysql.cur.fetchall()
        return jsonify({"book": book[0]}), 200
    else:
        return jsonify({"message": "failure"}), 401

@app.route('/bookdatarecommendations', methods=['GET'])
def getBookDataRecommentation():
    mysql = database.Database()
    book_id = request.args.get('id')
    result = mysql.getBookPageRecommendations(book_id)
    mysql.closeCursor()
    if len(result) > 0:
        return jsonify({"book_recommendations": result}), 200
    else:
        return jsonify({"message": "failure"}), 401

@app.route('/recommendations', methods=['GET'])
def getRecommendations():
    user_id = request.args.get('id')
    print("user id:", user_id)
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, int(user_id), token):
        mysql = database.Database()
        rec_list, len_rec_list = mysql.getRecommendationList(user_id)
        mysql.closeCursor()
        return jsonify({"recommendations": rec_list, "total_length": len_rec_list}), 200
    else:
        return jsonify({
        'message': 'Token is invalid !!'
    }), 401
    

@app.route('/mybooklist', methods=['GET'])
def getBooklist():
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, int(user_id), token):
        mysql = database.Database()
        result = mysql.getBooklist(user_id)
        if result > 0:
            bookListDetails = mysql.cur.fetchall()
            mysql.closeCursor()
            return jsonify({"booklist": bookListDetails}), 200
        else:
            mysql.closeCursor()
            return jsonify({"message": "No booklists found", "booklist": []}), 403
    return jsonify({
        'message': 'Token is invalid !!'
    }), 401


@app.route('/mybooklistwithdata', methods=['GET'])
def getBooklistWithData():
    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, int(user_id), token):
        result = mysql.getBooklistWithData(user_id)
        mysql.closeCursor()
        if len(result) == 0:
            return jsonify({"message": "No Booklists Found !!"}), 403
        return jsonify(result), 200
    return jsonify({
        'message': 'Token is invalid !!'
    }), 401


@app.route('/updatebooklistname', methods=['PUT'])
def updateBooklistName():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    booklist_id = payload['booklistId']
    booklist_name = payload['booklistName']
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        result = mysql.updateBooklistName(user_id, booklist_id, booklist_name)
        mysql.con.commit()
        mysql.closeCursor()
        if result > 0:
            return jsonify({"message": "success"}), 200
        return jsonify({"message": "Something went wrong, try again"}), 403

    return jsonify({"message": "Token is Invalid !!"}), 401


@app.route('/createbooklist', methods=['POST'])
def createBooklist():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    booklist_name = payload['booklistName']
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        result = mysql.createBooklist(user_id, booklist_name)
        mysql.con.commit()
        mysql.closeCursor()
        if result > 0:
            return jsonify({"message": "success"}), 200
        return jsonify({"message": "Something went wrong, try again"}), 403

    return jsonify({"message": "Token is Invalid !!"}), 401


@app.route('/createbooklistwithbook', methods=['POST'])
def createBooklistWithBook():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    booklist_name = payload['booklistName']
    book_id = payload['bookId']
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        result = mysql.createBooklistWithBook(
            user_id, booklist_name, book_id)
        mysql.con.commit()
        mysql.closeCursor()
        if result > 0:
            return jsonify({"message": "success"}), 200
        return jsonify({"message": "Something went wrong, try again"}), 403

    return jsonify({"message": "Token is Invalid !!"}), 401


@app.route('/deletefrombooklist', methods=['POST'])
def deleteFromBooklist():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    booklist_id = payload['booklistId']
    book_id = payload['bookId']
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        result = mysql.deleteFromBooklist(booklist_id, book_id)
        mysql.con.commit()
        mysql.closeCursor()
        if result > 0:
            return jsonify({"message": "success"}), 200
        return jsonify({"message": "Something went wrong, try again"}), 403

    return jsonify({"message": "Token is Invalid !!"}), 401


@app.route('/deletebooklist', methods=['POST'])
def deleteBooklist():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    booklist_id = payload['booklistId']
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        result = mysql.deleteBooklist(user_id, booklist_id)
        mysql.con.commit()
        mysql.closeCursor()
        if result > 0:
            return jsonify({"message": "success"}), 200
        return jsonify({"message": "Something went wrong, try again"}), 403

    return jsonify({"message": "Token is Invalid !!"}), 401


@app.route('/inserttobooklist', methods=['POST'])
def insertInBooklist():
    mysql = database.Database()
    payload = request.get_json()
    user_id = payload['userId']
    book_id = payload['bookId']
    booklist_id = payload['booklistId']
    token = request.headers['Authorization'].split(" ")[1]
    if maketoken.decode_token(app, user_id, token):
        result = mysql.insertInBooklist(booklist_id, book_id)
        mysql.con.commit()
        mysql.closeCursor()
        if result == 1:
            return jsonify({"message": "success"}), 200
        return jsonify({"message": "book already exists"}), 403

    return jsonify({"message": "Token is Invalid !!"}), 401


if __name__ == "__main__":
    app.run(debug=True)

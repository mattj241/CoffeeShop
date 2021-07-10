import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import sqlalchemy
from sqlalchemy.orm.session import close_all_sessions

from .database.models import db_drop_and_create_all, setup_db,\
    Drink, session_close, session_revert
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# CORS Headers 
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', \
                            'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', \
                            'GET,PUT,POST,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()


# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
        drinks_list = [drink.short() for drink in drinks]
        return jsonify({
            "success" : True,
            "drinks" : drinks_list
        })
    except Exception:
        abort (404)
    finally:
        session_close()


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detailed(jwt):
    try:
        drinks = Drink.query.all()
        drinks_list = [drink.long() for drink in drinks]
        return jsonify({
            "success" : True,
            "drinks" : drinks_list
        })
    except Exception:
        abort (404)
    finally:
        session_close()


# TODO states to "returns status code 200 and json {"success": True,
# "drinks":drink}where drink an array containing only the newly created drink".
# This goes against the frontend design to instantly add a drink to the UI.
# I will be leaving as the TODO says, but perhaps remove that in the future?
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def make_drink(jwt):
    data = request.get_json()
    try:
        formatted_title = data['title']
        recipe_list = (json.dumps(data['recipe']))
        # print(request.get_json())
        # print(recipe_list)
        new_drink = Drink(formatted_title, recipe_list)
        Drink.insert(new_drink)
        saved_drink = Drink.query.filter(Drink.title==new_drink.title).first()
        return jsonify({
            "success" : True,
            "drinks" : saved_drink.long()
        })
    except Exception:
        session_revert()
        abort(422)
    finally:
        session_close()


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    data = request.get_json()
    try:
        target_drink = Drink.query.filter(Drink.id==id).first()
        if "title" in data:
            target_drink.title = data['title']
        if "recipe" in data:
            target_drink.recipe = (json.dumps(data['recipe']))
        Drink.update(target_drink)
        updated_drink = Drink.query.filter(Drink.title == target_drink.title).first()
        return jsonify({
            "success" : True,
            "drinks" : updated_drink.long()
        })
    except sqlalchemy.orm.exc.UnmappedInstanceError:
        session_revert()
        abort(404)
    except TypeError:
        session_revert()
        abort(404)
    except AttributeError:
        session_revert()
        abort(404)
    except Exception:
        session_revert()
        abort(422)
    finally:
        session_close()

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    try:
        target_drink = Drink.query.filter(Drink.id==id).first()
        Drink.delete(target_drink)
        return jsonify({
            "success" : True,
            "delete" : id
        })
    except sqlalchemy.orm.exc.UnmappedInstanceError:
        session_revert()
        abort(404)
    except TypeError:
        session_revert()
        abort(404)
    finally:
        session_close()


@app.errorhandler(AuthError)
def AuthErrorHandler(error):
    return jsonify({
        "success": False,
        "error": error.description,
        "message": error.code['code']
    }), error.description

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401

    
@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
    }), 403
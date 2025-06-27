#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


class RestaurantsListResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants], 200


class RestaurantResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            return restaurant.to_dict(rules=("-restaurant_pizzas.restaurant",)), 200
        else:
            return {"error": "Restaurant not found"}, 404

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return "", 204
        else:
            return {"error": "Restaurant not found"}, 404


class PizzasListResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [pizza.to_dict(only=("id", "name", "ingredients")) for pizza in pizzas], 200


class RestaurantPizzaCreateResource(Resource):
    def post(self):
        data = request.get_json()
        price = data.get("price")
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")

        # Validate presence of required fields
        errors = []
        if price is None:
            errors.append("Price is required")
        if pizza_id is None:
            errors.append("Pizza ID is required")
        if restaurant_id is None:
            errors.append("Restaurant ID is required")

        if errors:
            return {"errors": errors}, 400

        # Check if pizza and restaurant exist
        pizza = Pizza.query.get(pizza_id)
        restaurant = Restaurant.query.get(restaurant_id)
        if not pizza:
            errors.append("Pizza not found")
        if not restaurant:
            errors.append("Restaurant not found")
        if errors:
            return {"errors": errors}, 400

        # Create RestaurantPizza
        try:
            restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
            db.session.add(restaurant_pizza)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400

        return restaurant_pizza.to_dict(), 201


api.add_resource(RestaurantsListResource, "/restaurants")
api.add_resource(RestaurantResource, "/restaurants/<int:id>")
api.add_resource(PizzasListResource, "/pizzas")
api.add_resource(RestaurantPizzaCreateResource, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)

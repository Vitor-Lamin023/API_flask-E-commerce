# importação
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS #permite que outros softwares acessem a sua API 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# instancia o aplicativo do flask 
app = Flask(__name__)
app.config['SECRET_KEY'] = "Minha_Chave_123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
login_manager = LoginManager()

db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app)

#modelagem - Colunas campos de informação / Linhas - Registros 
class User(db.Model,UserMixin):
   id = db.Column(db.Integer, primary_key=True)
   username = db.Column(db.String(80), nullable=False,unique=True)
   password = db.Column(db.String(80), nullable=True)
   cart = db.relationship('Cartitem', backref='user', lazy=True)
#exemplo: Produtos {id,name,price,descripition}


@app.route('/login', methods=["POST"])
def login():
   data = request.json  
   user = User.query.filter_by(username=data.get("username")).first()
   if user:
    if data.get("password") == user.password:
          login_user(user)
          return jsonify({"message": "logged in successfully"}) 
    return jsonify({"message": "unhauthorized. invalid credentials"}), 401

@app.route('/logout', methods=["POST"])
@login_required
def logout():
   logout_user()
   return jsonify({"message": "logout successfully"}) 
   


class Product(db.Model):

  id = db.Column(db.Integer, primary_key=True) #integer = inteiros 
  name = db.Column(db.String(128), nullable=False) #string = texto; {128} - limitação; nullable=False obrigatório
  price = db.Column(db.Float, nullable=False)  #float = números decimais
  descripition = db.Column(db.Text, nullable=True) # texto sem limitação  nullable=true - não é obrigatório


class Cartitem(db.Model):
   
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)



@login_manager.user_loader
def load_user(user_id):
   return User.query.get(int(user_id))
@app.route('/api/products/add', methods=["POST"])
@login_required
def add_products():
    data = request.json  

    if 'name' in data and 'price' in data:
        product = Product(
            name=data["name"],
            price=data["price"],
            descripition=data.get("descripition", "")  # nota: ainda está escrito "descripition"
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added successfully"}), 201

    return jsonify({"message": "Invalid product data"}), 400

@app.route('/api/products/delete/<int:product_id>', methods=["DELETE"])
@login_required
def delete_products(product_id):
    product = Product.query.get(product_id)  # salva o produto encontrado

    if product:  # verifica se encontrou
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"}), 200

    return jsonify({"message": "Product not found"}), 404

@app.route('/api/products/<int:product_id>', methods=["GET"])
def get_Products_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name":product.name,
            "price":product.price,
            "descripition":product.descripition
        }) 
    return jsonify({"menssage":"not found product"}), 404

@app.route('/api/products/update/<int:product_id>', methods=["PUT"])
@login_required
def update_products(product_id):
 product =  product = Product.query.get(product_id)
 if not product:
  return jsonify({"menssage":"not found product"}), 404
 

 data = request.json
 if 'name' in data:
    product.name = data['name']

 if 'price' in data:
    product.price = data['price']

 if 'descripition' in data:
    product.descripition= data['descripition']     

 db.session.commit()
 return jsonify({"menssage":"uptaded product sucessfully"})


@app.route('/api/products', methods=["GET"])
def get_products():
   products = Product.query.all()
   product_list =[]
   for product in products: 
    product_data =({
            "id": product.id,
            "name":product.name,
            "price":product.price,
            "descripition":product.descripition
        }) 
    product_list.append(product_data)
   return jsonify(product_list)
# rotas - Portas
# Definir uma rota raiz (Página inicial) e a função que será executada ao requisitar

#checkout
@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
   user = User.query.get(int(current_user.id))
   product = Product.query.get(product_id)

   if user and product:
    cart_item = Cartitem(user_id=user.id, product_id=product.id)
    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'added to the cart sucessfully'})
   return jsonify({'message': 'failed to add item to the cart'}), 400
   
@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
   cart_item = Cartitem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
   if cart_item:
      db.session.delete(cart_item)
      db.session.commit()
      return jsonify({'message': 'removed item to the cart sucessfully'})
   return jsonify({'message': 'removed to deleted item to the cart'}), 400

@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
   user = User.query.get(int(current_user.id))
   cart_items = user.cart
   cart_list = []
   
   for cart_item in cart_items:
      product = Product.query.get(cart_item.product_id)
      cart_list.append({
                        "id":cart_item.id,
                        "user_id":cart_item.user_id,
                        "product_id":cart_item.product_id,
                        "product_name":product.name,
                        "product_price":product.price
                       })

      print(cart_item)
      return jsonify({'message':cart_list})


@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
     user = User.query.get(int(current_user.id))
     cart_items = user.cart
     for cart_item in cart_items:
       db.session.delete(cart_item)
       db.session.commit()
     return jsonify({'message': 'checkout sucessfully'})
  


if __name__ == '__main__':
    app.run(debug=True)

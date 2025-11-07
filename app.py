from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://expense_user:HariBahadur@localhost:5432/expenses_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    expenses = db.relationship('Expense', backref='category', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


with app.app_context():
    db.create_all()
    
    
    default_categories = ['Food', 'Transport', 'Entertainment', 'Utilities', 'Other']
    for cat_name in default_categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    db.session.commit()


@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    categories = Category.query.all()
    
   
    total = sum(expense.amount for expense in expenses)
    
    chart_data = {}
    for category in categories:
        category_total = sum(exp.amount for exp in category.expenses)
        if category_total > 0:
            chart_data[category.name] = category_total
    
    return render_template('index.html', 
                         expenses=expenses, 
                         categories=categories,
                         total=total,
                         chart_data=chart_data)

@app.route('/add', methods=['POST'])
def add_expense():
    amount = float(request.form['amount'])
    description = request.form['description']
    category_id = int(request.form['category'])
    
    new_expense = Expense(
        amount=amount,
        description=description,
        category_id=category_id
    )
    
    db.session.add(new_expense)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/dump')
def dump_data():
    expenses = Expense.query.all()
    data = []
    
    for expense in expenses:
        data.append({
            'id': expense.id,
            'amount': expense.amount,
            'description': expense.description,
            'date': expense.date.isoformat(),
            'category': expense.category.name
        })
    
    
    os.makedirs('data', exist_ok=True)
    
  
    filename = f'data/expenses_dump_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return f"Data dumped to {filename}. <a href='/'>Go back</a>"

if __name__ == '__main__':
    app.run(debug=True)
import os,csv,io
from datetime import datetime
from flask import Flask,render_template,request,redirect,url_for,flash,jsonify,Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.security import generate_password_hash,check_password_hash
app=Flask(__name__);app.config['SECRET_KEY']=os.getenv('SECRET_KEY','dev-change-this-secret');app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('DATABASE_URL','sqlite:///inventory.db');app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app);login_manager=LoginManager(app);login_manager.login_view='login';login_manager.login_message_category='warning'
class User(UserMixin,db.Model):
 id=db.Column(db.Integer,primary_key=True);email=db.Column(db.String(180),unique=True,nullable=False);password_hash=db.Column(db.String(255),nullable=False);role=db.Column(db.String(30),default='admin');created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Category(db.Model):
 id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(120),unique=True,nullable=False);products=db.relationship('Product',backref='category',lazy=True)
class Supplier(db.Model):
 id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(180),nullable=False);email=db.Column(db.String(180));phone=db.Column(db.String(80));products=db.relationship('Product',backref='supplier',lazy=True)
class Product(db.Model):
 id=db.Column(db.Integer,primary_key=True);sku=db.Column(db.String(80),unique=True,nullable=False);name=db.Column(db.String(180),nullable=False);category_id=db.Column(db.Integer,db.ForeignKey('category.id'));supplier_id=db.Column(db.Integer,db.ForeignKey('supplier.id'));quantity=db.Column(db.Integer,default=0,nullable=False);reorder_level=db.Column(db.Integer,default=5,nullable=False);unit_price=db.Column(db.Float,default=0.0,nullable=False);location=db.Column(db.String(120),default='Main Store');active=db.Column(db.Boolean,default=True);created_at=db.Column(db.DateTime,default=datetime.utcnow);updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
class StockMovement(db.Model):
 id=db.Column(db.Integer,primary_key=True);product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False);movement_type=db.Column(db.String(20),nullable=False);quantity=db.Column(db.Integer,nullable=False);note=db.Column(db.String(255));created_by=db.Column(db.String(180));created_at=db.Column(db.DateTime,default=datetime.utcnow);product=db.relationship('Product',backref='movements')
class AuditLog(db.Model):
 id=db.Column(db.Integer,primary_key=True);action=db.Column(db.String(120),nullable=False);details=db.Column(db.String(500));user_email=db.Column(db.String(180));created_at=db.Column(db.DateTime,default=datetime.utcnow)
@login_manager.user_loader
def load_user(user_id): return db.session.get(User,int(user_id))
def audit(action,details=''):
 db.session.add(AuditLog(action=action,details=details,user_email=getattr(current_user,'email','system')));db.session.commit()
def ensure_seed():
 db.create_all()
 if not User.query.first(): db.session.add(User(email=os.getenv('ADMIN_EMAIL','admin@integratortool.com'),password_hash=generate_password_hash(os.getenv('ADMIN_PASSWORD','Admin@123')),role='admin'))
 if not Category.query.first(): db.session.add_all([Category(name=x) for x in ['CCTV','Networking','LED Display','Access Control','Accessories']])
 if not Supplier.query.first(): db.session.add_all([Supplier(name='Primary Distributor',email='sales@example.com',phone='+966 55 000 0001'),Supplier(name='Local Supplier',email='orders@example.com',phone='+966 55 000 0002')])
 db.session.commit()
 if not Product.query.first():
  cats={c.name:c for c in Category.query.all()};s=Supplier.query.all();db.session.add_all([
   Product(sku='CAM-8MP-001',name='8MP IP Camera',category=cats['CCTV'],supplier=s[0],quantity=24,reorder_level=10,unit_price=395,location='A-01'),
   Product(sku='SW-POE-024',name='24-Port PoE Switch',category=cats['Networking'],supplier=s[0],quantity=6,reorder_level=5,unit_price=780,location='B-03'),
   Product(sku='LED-P25-001',name='Indoor LED Module P2.5',category=cats['LED Display'],supplier=s[1],quantity=80,reorder_level=20,unit_price=145,location='C-02'),
   Product(sku='ACC-CTRL-01',name='Access Controller',category=cats['Access Control'],supplier=s[1],quantity=3,reorder_level=5,unit_price=620,location='D-04')]);db.session.commit()
@app.before_request
def init_once(): ensure_seed()
@app.route('/login',methods=['GET','POST'])
def login():
 if current_user.is_authenticated:return redirect(url_for('dashboard'))
 if request.method=='POST':
  u=User.query.filter_by(email=request.form.get('email','').strip().lower()).first()
  if u and check_password_hash(u.password_hash,request.form.get('password','')): login_user(u);return redirect(url_for('dashboard'))
  flash('Invalid email or password.','danger')
 return render_template('login.html')
@app.route('/logout')
@login_required
def logout(): logout_user();return redirect(url_for('login'))
@app.route('/')
@login_required
def dashboard():
 ps=Product.query.filter_by(active=True).all();low=[p for p in ps if p.quantity<=p.reorder_level];recent=StockMovement.query.order_by(StockMovement.created_at.desc()).limit(8).all();return render_template('dashboard.html',total_products=len(ps),total_units=sum(p.quantity for p in ps),stock_value=sum(p.quantity*p.unit_price for p in ps),low_stock=low,recent=recent)
@app.route('/products')
@login_required
def products():
 q=request.args.get('q','').strip();cid=request.args.get('category',type=int);query=Product.query.filter_by(active=True)
 if q: query=query.filter(db.or_(Product.name.ilike(f'%{q}%'),Product.sku.ilike(f'%{q}%')))
 if cid:query=query.filter_by(category_id=cid)
 items=query.order_by(Product.name).all()
 if request.args.get('low')=='1':items=[p for p in items if p.quantity<=p.reorder_level]
 return render_template('products.html',products=items,categories=Category.query.order_by(Category.name).all(),suppliers=Supplier.query.order_by(Supplier.name).all())
@app.route('/products/add',methods=['POST'])
@login_required
def product_add():
 sku=request.form['sku'].strip();name=request.form['name'].strip()
 if Product.query.filter_by(sku=sku).first():flash('SKU already exists.','danger');return redirect(url_for('products'))
 p=Product(sku=sku,name=name,category_id=request.form.get('category_id',type=int),supplier_id=request.form.get('supplier_id',type=int),quantity=max(0,request.form.get('quantity',type=int) or 0),reorder_level=max(0,request.form.get('reorder_level',type=int) or 0),unit_price=max(0,request.form.get('unit_price',type=float) or 0),location=request.form.get('location','Main Store').strip());db.session.add(p);db.session.commit();audit('PRODUCT_CREATED',f'{p.sku} - {p.name}');flash('Product added successfully.','success');return redirect(url_for('products'))
@app.route('/products/<int:pid>/edit',methods=['POST'])
@login_required
def product_edit(pid):
 p=db.session.get(Product,pid)
 if not p:return('Not found',404)
 p.name=request.form['name'].strip();p.category_id=request.form.get('category_id',type=int);p.supplier_id=request.form.get('supplier_id',type=int);p.reorder_level=max(0,request.form.get('reorder_level',type=int) or 0);p.unit_price=max(0,request.form.get('unit_price',type=float) or 0);p.location=request.form.get('location','').strip();db.session.commit();audit('PRODUCT_UPDATED',f'{p.sku} - {p.name}');flash('Product updated.','success');return redirect(url_for('products'))
@app.route('/products/<int:pid>/delete',methods=['POST'])
@login_required
def product_delete(pid):
 p=db.session.get(Product,pid)
 if not p:return('Not found',404)
 p.active=False;db.session.commit();audit('PRODUCT_DEACTIVATED',f'{p.sku} - {p.name}');flash('Product deactivated.','warning');return redirect(url_for('products'))
@app.route('/stock')
@login_required
def stock(): return render_template('stock.html',products=Product.query.filter_by(active=True).order_by(Product.name).all(),movements=StockMovement.query.order_by(StockMovement.created_at.desc()).limit(100).all())
@app.route('/stock/move',methods=['POST'])
@login_required
def stock_move():
 p=db.session.get(Product,request.form.get('product_id',type=int));typ=request.form.get('movement_type');qty=request.form.get('quantity',type=int) or 0
 if not p or qty<=0 or typ not in {'IN','OUT','ADJUST'}:flash('Invalid stock movement.','danger');return redirect(url_for('stock'))
 if typ=='IN':p.quantity+=qty
 elif typ=='OUT':
  if qty>p.quantity:flash('Insufficient stock.','danger');return redirect(url_for('stock'))
  p.quantity-=qty
 else:p.quantity=qty
 db.session.add(StockMovement(product_id=p.id,movement_type=typ,quantity=qty,note=request.form.get('note','').strip(),created_by=current_user.email));db.session.commit();audit('STOCK_MOVEMENT',f'{p.sku}: {typ} {qty}');flash('Stock updated.','success');return redirect(url_for('stock'))
@app.route('/suppliers',methods=['GET','POST'])
@login_required
def suppliers():
 if request.method=='POST':
  s=Supplier(name=request.form['name'].strip(),email=request.form.get('email','').strip(),phone=request.form.get('phone','').strip());db.session.add(s);db.session.commit();audit('SUPPLIER_CREATED',s.name);flash('Supplier added.','success');return redirect(url_for('suppliers'))
 return render_template('suppliers.html',suppliers=Supplier.query.order_by(Supplier.name).all())
@app.route('/audit')
@login_required
def audit_log(): return render_template('audit.html',logs=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all())
@app.route('/export/products.csv')
@login_required
def export_products():
 s=io.StringIO();w=csv.writer(s);w.writerow(['SKU','Product','Category','Supplier','Quantity','Reorder Level','Unit Price','Location'])
 for p in Product.query.filter_by(active=True).order_by(Product.name).all():w.writerow([p.sku,p.name,p.category.name if p.category else '',p.supplier.name if p.supplier else '',p.quantity,p.reorder_level,f'{p.unit_price:.2f}',p.location])
 return Response(s.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=inventory-products.csv'})
@app.route('/api/health')
def api_health(): return jsonify(status='healthy',service='integrator-inventory',timestamp=datetime.utcnow().isoformat()+'Z')
@app.route('/api/summary')
@login_required
def api_summary():
 ps=Product.query.filter_by(active=True).all();return jsonify(total_products=len(ps),total_units=sum(p.quantity for p in ps),low_stock=sum(1 for p in ps if p.quantity<=p.reorder_level),stock_value=round(sum(p.quantity*p.unit_price for p in ps),2))
if __name__=='__main__':
 with app.app_context():ensure_seed()
 app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')),debug=os.getenv('FLASK_DEBUG')=='1')

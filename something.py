from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

#create app
app = Flask(__name__)

#configuration my app
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.sqlite3'
app.config['SECRET_KEY'] = 'myproject2'

#initialize packages
mydb = SQLAlchemy(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))


#defining schemas for my app
class Messages(mydb.Model):
    id = mydb.Column(mydb.Integer, primary_key=True)
    emailid = mydb.Column(mydb.String(120), nullable=False)
    status = mydb.Column(mydb.String(50), nullable=False)
    comment = mydb.Column(mydb.String(1000), nullable=False)

class Users(mydb.Model, UserMixin):
    id = mydb.Column(mydb.Integer, primary_key=True)
    emailid = mydb.Column(mydb.String(120), unique=True)
    password = mydb.Column(mydb.String(120), nullable=False)
    fullname = mydb.Column(mydb.String(120), nullable=False)
    post = mydb.relationship('Posts', backref="users")

class Posts(mydb.Model):
    id = mydb.Column(mydb.Integer, primary_key=True)
    title = mydb.Column(mydb.String(500), nullable=False)
    tags = mydb.Column(mydb.String(500), nullable=False)
    article = mydb.Column(mydb.String(4000), nullable=False)
    emailid = mydb.Column(mydb.String(120), mydb.ForeignKey('users.emailid'))



#defining routes as following

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('emailid')
        label = request.form.get('label')
        msg = request.form.get('message')
        new_feed = Messages(emailid = email, status = label, comment = msg)
        mydb.session.add(new_feed)
        mydb.session.commit()
        flash("Feeback Uploaded", category = 'success')
        return redirect(url_for("home"))
    postdetails = Posts.query.order_by(desc(Posts.id)).limit(10).all()
    feedbacks = Messages.query.order_by(desc(Messages.id)).all()
    return render_template("home.html",userdetails= current_user, postdetails = postdetails,feedbacks = feedbacks)


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('emailid')
        fullname = request.form.get('fullname')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = Users.query.filter_by(emailid = email).first()
        if user :
            flash("Email already Exists.", category = 'error')
        elif len(email) < 4:
            flash("Email must be greater than 3 characters.", category = 'error')
        elif len(fullname) < 2:
            flash("Full name must be greater than 2 characters", category = 'error')
        elif password1 != password2:
            flash("Password does not match", category = 'error')
        elif len(password1) < 7 :
            flash("Password must be greater than 7 characters", category = 'error')
        else:
            new_user = Users(emailid=email, password=generate_password_hash(password1, method='sha256'), fullname=fullname,)
            mydb.session.add(new_user)
            mydb.session.commit()
            flash("Account Created ! Login to continue")
            return redirect(url_for('login'))   
    return render_template('signup.html', userdetails = current_user)



@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('loginemailid')
        password = request.form.get('checkpassword')
        user = Users.query.filter_by(emailid = email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in Successfully !", category = 'success')
                login_user(user, remember = True)
                return redirect(url_for('myprofile'))
            else:
                flash("Password incorrect !", category = 'error')
        else:
            flash("Account doesn't Exists ! Please create an account first", category = 'error')
    return render_template('login.html',userdetails=current_user)
    


@app.route('/myprofile', methods = ['GET','POST'])
@login_required
def myprofile():
    postdetails = Posts.query.filter_by(emailid = current_user.emailid).order_by(desc(Posts.id)).all()
    userid = current_user.id
    userdetails = Users.query.filter_by(id = userid).first()

    if request.method == 'POST':
        title = request.form.get('title')
        tags = request.form.get('description')
        article = request.form.get('article')
        new_post = Posts(title=title, tags=tags, article=article, emailid=current_user.emailid)
        mydb.session.add(new_post)
        mydb.session.commit()
        flash("Post Uploaded !")
        return redirect(url_for('myprofile'))
    return render_template('myprofile.html',userdetails=current_user,postdetails=postdetails)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("LoggedOut Seccessfully", category = 'success')
    return redirect(url_for('home'))


@app.route('/allarticles')
def allarticles():
    postdetails = Posts.query.order_by(desc(Posts.id)).all()
    return render_template('allarticles.html',userdetails=current_user,postdetails=postdetails)


@app.route('/fullarticle/<postid>', methods = ['GET'])
def fullarticle(postid):
    postdetails = Posts.query.filter_by(id = postid).first()
    return render_template("fullarticle.html",userdetails = current_user,postdetails=postdetails)


@app.errorhandler(401)
def not_found_error(error):
    return redirect(url_for('signup')), 401

if __name__ == '__main__':
    app.run(debug=True)
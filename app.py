from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__)

app.secret_key = "super-secret-change-this"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Admin(UserMixin):
    id = 1
    username = "admin"
    password = "password123"  # change this later

@login_manager.user_loader
def load_user(user_id):
    return Admin()

from flask_mail import Mail, Message

# Email config (Gmail SMTP)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "andrew.willis.swartz@gmail.com"
app.config["MAIL_PASSWORD"] = "qpzi cmlq bbtv xgdk"
app.config["MAIL_DEFAULT_SENDER"] = "andrew.willis.swartz@gmail.com"

mail = Mail(app)

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leads.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Lead model
class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    zillow_value = db.Column(db.Integer)
    repair_cost = db.Column(db.Integer)
    offer_low = db.Column(db.Integer)
    offer_high = db.Column(db.Integer)


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        lead = Lead(
            name=request.form["name"],
            phone=request.form["phone"],
            email=request.form.get("email"),
            address=request.form.get("address"),
            message=request.form.get("message"),
        )
        db.session.add(lead)
        db.session.commit()
        
        msg = Message(
            subject="New Property Lead Submitted",
            recipients=["andrew.willis.swartz@gmail.com"]
        )
        msg.body = f"""
        New Lead Submitted:

        Name: {lead.name}
        Phone: {lead.phone}
        Email: {lead.email}
        Address: {lead.address}
        Message: {lead.message}
        Submitted: {lead.created_at}
        """
        mail.send(msg)


        return redirect(url_for("thank_you"))

    return render_template("contact.html")

@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")

@app.route("/admin/leads")
@login_required
def admin_leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("admin_leads.html", leads=leads)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == Admin.username and password == Admin.password:
            login_user(Admin())
            return redirect(url_for("admin_leads"))

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/offer", methods=["GET", "POST"])
def offer():
    if request.method == "POST":
        address = request.form["address"]
        zillow_value = int(request.form["zillow_value"])

        # Repair costs from checkboxes
        repairs = request.form.getlist("repairs")
        repair_total = sum(int(r) for r in repairs)

        # --- Offer Calculation Logic ---
        base_offer = int(zillow_value * 0.75)
        final_offer = base_offer - repair_total

        offer_low = int(final_offer * 0.95)
        offer_high = int(final_offer * 1.05)

        return render_template(
            "offer_result.html",
            address=address,
            zillow_value=zillow_value,
            repair_total=repair_total,
            offer_low=offer_low,
            offer_high=offer_high
        )

    return render_template("offer.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/areas/<city>")
def area_page(city):
    city_data = {
        "allentown": {
            "name": "Allentown",
            "headline": "We Buy Houses in Allentown, PA",
            "content": """
Allentown homeowners often face situations where listing traditionally isn’t the best option.
Whether your home needs repairs, you inherited a property, or you simply want a fast and stress-free sale,
Dadlife Property Solutions provides fair, honest solutions for selling your home as-is.

We handle the paperwork, cover closing costs, and work on your timeline. No agents, no showings,
and no uncertainty. Our goal is to create a win-win solution for every Allentown family we work with.
"""
        },
        "bethlehem": {
            "name": "Bethlehem",
            "headline": "Sell Your Home Fast in Bethlehem, PA",
            "content": """
Selling a home in Bethlehem can feel overwhelming, especially if repairs or life changes are involved.
We help homeowners sell quickly and conveniently without listing on the market.

At Dadlife Property Solutions, we’re a local family business. We treat every homeowner with honesty,
respect, and transparency while providing a simple, stress-free selling experience.
"""
        },
        "easton": {
            "name": "Easton",
            "headline": "Cash Home Buyers in Easton, PA",
            "content": """
If you need to sell a property in Easton without delays or expensive repairs,
we offer fast and fair home-buying solutions.

Our process is straightforward: tell us about your property, receive an honest offer,
and close on your timeline. No pressure — just clear answers and local service you can trust.
"""
        }
    }

    city = city.lower()
    if city not in city_data:
        return "City not found", 404

    return render_template("area.html", city=city_data[city])

@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")

@app.route("/projects")
def projects():
    return render_template("projects.html")

@app.route("/book")
def book():
    return render_template("book.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


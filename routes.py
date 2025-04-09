import os
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Hospital, BloodBank, BloodRequest, RequestStatusEnum, UrgencyLevelEnum, BloodTypeEnum, BloodInventory
from datetime import datetime

def init_routes(app):
    @app.route("/", methods=["GET"])
    def homepage():
        return render_template("homepage.html")

    ############################## Hospital Routes ####################################

    @app.route("/register_hospital", methods=["GET", "POST"])
    def register_hospital():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")  # Correctly fetching password
            address = request.form.get("address")
            pincode = request.form.get("pincode")
            license_number = request.form.get("license_number")
            phone_number = request.form.get("phone_number")

            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash("Username or Email already taken!", "danger")
                return redirect(url_for("register_hospital"))

            hashed_pass = generate_password_hash(password)  # Hash password

            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_pass,  # Fix: Using correct field name
                address=address,
                pincode=pincode,
                user_type="hospital"
            )
            db.session.add(new_user)
            db.session.commit()

            new_hospital = Hospital(
                user_id=new_user.id,
                name=username,
                license_number=license_number,
                phone_number=phone_number,
                address=address,
                pincode=pincode
            )
            db.session.add(new_hospital)
            db.session.commit()

            flash("Hospital successfully registered. Please log in.", "success")
            return redirect(url_for("login_hospital"))
        return render_template("register_hospital.html")

    @app.route("/login_hospital", methods=["GET", "POST"])
    def login_hospital():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter_by(username=username, user_type="hospital").first()
            if user and check_password_hash(user.password_hash, password):  # Fix: Using `password_hash`
                session["user_id"] = user.id
                session["username"] = user.username
                session["user_type"] = "hospital"

                flash("Login successful", "success")
                return redirect(url_for("hospital_dashboard"))

            flash("Login unsuccessful, please check username and password", "danger")  
        return render_template("login_hospital.html")  
        
    @app.route("/hospital_dashboard")
    def hospital_dashboard():
        if "user_id" not in session or session.get("user_type") != "hospital":
            flash("Please log in to access the dashboard", "warning")
            return redirect(url_for("login_hospital"))

        hospital = Hospital.query.filter_by(user_id=session["user_id"]).first()
        if not hospital:
            flash("Invalid session. Please log in again.", "danger")
            session.clear()
            return redirect(url_for("login_hospital"))

        return render_template("hospital_dashboard.html", hospital=hospital)
    
    
    
    @app.route("/search_blood", methods=["GET", "POST"])
    def search_blood():
        if "user_id" not in session or session.get("user_type") != "hospital":
            flash("You must be logged in as a hospital to request blood.", "danger")
            return redirect(url_for("login_hospital"))

        hospital = Hospital.query.filter_by(user_id=session["user_id"]).first()

        if not hospital:
            flash("Hospital not found.", "danger")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            blood_type = request.form.get("blood_type")
            quantity_ml = int(request.form.get("quantity_ml"))

        # Query blood banks that have the requested blood
            available_banks = db.session.query(
            BloodBank.id, BloodBank.name, BloodBank.phone_number, BloodBank.address, 
            BloodInventory.quantity_ml
        ).join(BloodInventory).filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_ml >= quantity_ml
        ).all()

            blood_banks = [
            {
                "id": bank.id,
                "name": bank.name,
                "phone_number": bank.phone_number,
                "address": bank.address,
                "available_quantity": bank.quantity_ml
            }
                for bank in available_banks
        ]

            return render_template(
            "hospital_blood_request.html", 
            blood_banks=blood_banks, 
            searched=True, 
            requested_blood_type=blood_type, 
            requested_quantity=quantity_ml
        )
        flash("Your blood request has been submitted and is being processed.", "success")
        return render_template("hospital_blood_request.html", searched=False)
    @app.route("/create_blood_request/<int:blood_bank_id>", methods=["POST"])
    def create_blood_request(blood_bank_id):
        if "user_id" not in session or session.get("user_type") != "hospital":
            flash("You must be logged in as a hospital to create a request.", "danger")
            return redirect(url_for("login_hospital"))

        hospital = Hospital.query.filter_by(user_id=session["user_id"]).first()
        if not hospital:
            flash("Hospital not found.", "danger")
            return redirect(url_for("dashboard"))

        blood_type = request.form.get("blood_type")
        quantity_ml = int(request.form.get("quantity_ml"))

        new_request = BloodRequest(
        hospital_id=hospital.id,
        blood_bank_id=blood_bank_id,
        blood_type=blood_type,
        quantity_ml=quantity_ml,
        required_by_date=datetime.utcnow(),
        status="pending",
        urgency_level="normal"
    )

        db.session.add(new_request)
        db.session.commit()

        flash("Blood request submitted successfully!", "success")
        return redirect(url_for("search_blood"))
    
    @app.route("/hospital_profile")
    def hospital_profile():
        if "user_id" not in session or session.get("user_type") != "hospital":
            flash("Please log in to view your hospital profile.", "warning")
            return redirect(url_for("login_hospital"))

        user = User.query.get(session["user_id"])
        hospital = Hospital.query.filter_by(user_id=user.id).first()

        return render_template("hospital_profile.html", user=user, hospital=hospital)


    @app.route("/edit_hospital_profile", methods=["GET", "POST"])
    def edit_hospital_profile():
        if "user_id" not in session or session.get("user_type") != "hospital":
            flash("Please log in to edit your hospital profile.", "warning")
            return redirect(url_for("login_hospital"))

        hospital = Hospital.query.filter_by(user_id=session["user_id"]).first()

        if request.method == "POST":
            hospital.address = request.form.get("address")
            hospital.pincode = request.form.get("pincode")
            hospital.phone_number = request.form.get("phone_number")
            db.session.commit()
            flash("Hospital profile updated successfully!", "success")
            return redirect(url_for("hospital_profile"))

        return render_template("edit_hospital_profile.html", hospital=hospital)


    ############################## Hospital Contact ####################################
    @app.route("/hospital_contact", methods=["GET", "POST"])
    def hospital_contact():
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            message = request.form.get("message")

            # Log message for future DB connection
            print(f"Hospital Message from {name} ({email}): {message}")
            flash("Thank you for reaching out! We will get back to you soon.", "success")
            return redirect(url_for("hospital_contact"))

        return render_template("hospital_contact.html")

    
    
    

    ############################## Blood Bank Routes ####################################

    @app.route("/register_bloodbank", methods=["GET", "POST"])
    def register_bloodbank():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")  # Correctly fetching password
            address = request.form.get("address")
            pincode = request.form.get("pincode")
            license_number = request.form.get("license_number")
            phone_number = request.form.get("phone_number")
            name = request.form.get("name") or username

            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash("Username or Email already taken!", "danger")
                return redirect(url_for("register_bloodbank"))

            hashed_pass = generate_password_hash(password)  # Hash password

            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_pass,  # Fix: Using correct field name
                address=address,
                pincode=pincode,
                user_type="blood_bank"
            )
            db.session.add(new_user)
            db.session.commit()

            new_bloodbank = BloodBank(
                user_id=new_user.id,
                name=name,
                license_number=license_number,
                phone_number=phone_number,
                address=address,
                pincode=pincode
            )
            db.session.add(new_bloodbank)
            db.session.commit()

            flash("Blood bank successfully registered. Please log in.", "success")
            return redirect(url_for("login_bloodbank"))
        return render_template("register_bloodbank.html")

    @app.route("/login_bloodbank", methods=["GET", "POST"])
    def login_bloodbank():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter_by(username=username, user_type="blood_bank").first()
            if user and check_password_hash(user.password_hash, password):  # Fix: Using `password_hash`
                session["user_id"] = user.id
                session["username"] = user.username
                session["user_type"] = "blood_bank"

                flash("Login successful", "success")
                return redirect(url_for("bloodbank_dashboard"))

            flash("Login unsuccessful, please check username and password", "danger")
        return render_template("login_bloodbank.html")

    @app.route("/bloodbank_dashboard")
    def bloodbank_dashboard():
        if "user_id" not in session or session.get("user_type") != "blood_bank":
            flash("Please log in to access the dashboard", "warning")
            return redirect(url_for("login_bloodbank"))

        bloodbank = BloodBank.query.filter_by(user_id=session["user_id"]).first()
        if not bloodbank:
            flash("Invalid session. Please log in again.", "danger")
            session.clear()
            return redirect(url_for("login_bloodbank"))

        return render_template("bloodbank_dashboard.html", bloodbank=bloodbank)

        
  


    @app.route("/bloodbank_inventory", methods=["GET", "POST"])
    def bloodbank_inventory():
        if "user_id" not in session:
            flash("Please log in to access inventory.", "warning")
            return redirect(url_for("login"))

        user = User.query.get(session["user_id"])
    
        if not user or user.user_type != "blood_bank":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("dashboard"))

        blood_bank = BloodBank.query.filter_by(user_id=user.id).first()

        if not blood_bank:
            flash("Blood bank profile not found.", "danger")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            blood_type = request.form["blood_type"]
            quantity_ml = int(request.form["quantity_ml"])
            expiration_date = request.form["expiration_date"]

            existing_inventory = BloodInventory.query.filter_by(blood_bank_id=blood_bank.id, blood_type=blood_type).first()

            if existing_inventory:
                existing_inventory.quantity_ml += quantity_ml  # Update quantity
                existing_inventory.expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            else:
                new_inventory = BloodInventory(
                blood_bank_id=blood_bank.id,
                blood_type=blood_type,
                quantity_ml=quantity_ml,
                expiration_date=datetime.strptime(expiration_date, "%Y-%m-%d"),
            )
                db.session.add(new_inventory)

            db.session.commit()
            flash("Inventory updated successfully!", "success")

        return render_template("bloodbank_inventory.html", blood_bank=blood_bank, blood_types=BloodTypeEnum)

    @app.route("/add_inventory/<int:blood_bank_id>", methods=["GET", "POST"])
    def add_inventory(blood_bank_id):
        blood_bank = BloodBank.query.get_or_404(blood_bank_id)

        if request.method == "POST":
            blood_type = request.form["blood_type"]
            quantity_ml = int(request.form["quantity_ml"])
            expiration_date = request.form["expiration_date"]

            # Check if blood type already exists in inventory
            existing_inventory = BloodInventory.query.filter_by(blood_bank_id=blood_bank_id, blood_type=blood_type).first()
        
            if existing_inventory:
                existing_inventory.quantity_ml += quantity_ml  # Update quantity
                existing_inventory.expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            else:
                new_inventory = BloodInventory(
                    blood_bank_id=blood_bank_id,
                    blood_type=blood_type,
                    quantity_ml=quantity_ml,
                    expiration_date=datetime.strptime(expiration_date, "%Y-%m-%d"))
                db.session.add(new_inventory)

                db.session.commit()
                flash("Inventory updated successfully!", "success")
            return redirect(url_for("bloodbank_inventory"))

        return render_template("add_inventory.html", blood_bank=blood_bank, blood_types=BloodTypeEnum)

    @app.route("/view_requests" , methods=["GET"])
    def view_requests():
        if "user_id" not in session or session.get("user_type") != "blood_bank":
            flash("You must be logged in as a blood bank to view requests.", "danger")
            return redirect(url_for("login_bloodbank"))

    # Get the blood bank that is logged in
        blood_bank = BloodBank.query.filter_by(user_id=session["user_id"]).first()

        if not blood_bank:
            flash("Blood bank not found.", "danger")
            return redirect(url_for("dashboard"))
        
        pending_requests = BloodRequest.query.filter_by(blood_bank_id=blood_bank.id, status="pending").all()
        approved_requests = BloodRequest.query.filter_by(blood_bank_id=blood_bank.id, status="approved").all()
        rejected_requests = BloodRequest.query.filter_by(blood_bank_id=blood_bank.id, status="rejected").all()

    # Fetch all blood requests for this blood bank
        blood_requests = BloodRequest.query.filter_by(blood_bank_id=blood_bank.id).order_by(BloodRequest.status).all()

        return render_template("view_requests.html", blood_requests=blood_requests, pending_requests=pending_requests, approved_requests=approved_requests, rejected_requests=rejected_requests)

    @app.route("/update_request_status/<int:request_id>", methods=["POST"])
    def update_request_status(request_id):
        if "user_id" not in session or session.get("user_type") != "blood_bank":
            flash("You must be logged in as a blood bank to update requests.", "danger")
            return redirect(url_for("login_bloodbank"))

        request_entry = BloodRequest.query.get(request_id)

        if not request_entry:
            flash("Request not found.", "danger")
            return redirect(url_for("view_requests"))

        new_status = request.form.get("status")

    # ✅ Ensure the status matches the allowed enum values
        if new_status in ["pending", "approved", "rejected", "fulfilled", "cancelled"]:  
            request_entry.status = new_status
            db.session.commit()
            flash("Request status updated successfully!", "success")
        else:
            flash("Invalid status update.", "danger")

        return redirect(url_for("view_requests"))
    @app.route("/dispatch_blood/<int:request_id>", methods=["POST"])
    def dispatch_blood(request_id):  
        if "user_id" not in session or session.get("user_type") != "blood_bank":
            flash("You must be logged in as a blood bank to dispatch blood.", "danger")
            return redirect(url_for("login_bloodbank"))

        blood_request = BloodRequest.query.get(request_id)
    
        if not blood_request or blood_request.status != "approved":
            flash("Invalid or already processed request.", "danger")
            return redirect(url_for("view_requests"))

    # Update status to fulfilled (or dispatched)
        blood_request.status = "fulfilled"
        db.session.commit()

        flash("Blood dispatched successfully!", "success")
        return redirect(url_for("view_requests"))
    
    @app.route("/bloodbank_profile")
    def bloodbank_profile():
        if "user_id" not in session or session.get("user_type") != "blood_bank":
            flash("Please log in to view your blood bank profile.", "warning")
            return redirect(url_for("login_bloodbank"))

        user = User.query.get(session["user_id"])
        blood_bank = BloodBank.query.filter_by(user_id=user.id).first()

        return render_template("bloodbank_profile.html", user=user, blood_bank=blood_bank)


    @app.route("/edit_bloodbank_profile", methods=["GET", "POST"])
    def edit_bloodbank_profile():
        if "user_id" not in session or session.get("user_type") != "blood_bank":
            flash("Please log in to edit your blood bank profile.", "warning")
            return redirect(url_for("login_bloodbank"))

        blood_bank = BloodBank.query.filter_by(user_id=session["user_id"]).first()

        if request.method == "POST":
            blood_bank.address = request.form.get("address")
            blood_bank.pincode = request.form.get("pincode")
            blood_bank.phone_number = request.form.get("phone_number")
            db.session.commit()
            flash("Blood Bank profile updated successfully!", "success")
            return redirect(url_for("bloodbank_profile"))

        return render_template("edit_bloodbank_profile.html", blood_bank=blood_bank)


    ############################## Blood Bank Contact ####################################
    @app.route("/bloodbank_contact", methods=["GET", "POST"])
    def bloodbank_contact():
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            message = request.form.get("message")

            # Log message for future DB connection
            print(f"Blood Bank Message from {name} ({email}): {message}")
            flash("Thank you for reaching out! We will get back to you soon.", "success")
            return redirect(url_for("bloodbank_contact"))

        return render_template("bloodbank_contact.html")
 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("homepage"))
    
    
    

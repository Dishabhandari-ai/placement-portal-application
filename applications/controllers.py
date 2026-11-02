from flask import redirect,render_template,url_for,request
from jinja2 import Template 
from datetime import datetime
from flask import session
from flask_login import login_user, login_required, logout_user, current_user

from flask import current_app as app

from .model import *

@app.route("/login", methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        email= request.form.get("email")
        password = request.form.get("password")
     
        role = request.form.get("role")
        session["role"] = role 
        if not email or not password:
           return "All fields required"

        if role == "admin":
            this_user = Admin.query.filter_by(email=email).first()
        elif role == "student":
            this_user = Student.query.filter_by(email=email).first()
            
        elif role == "company":
            this_user = Company.query.filter_by(email=email).first()
  
        if this_user:
            if this_user.password == password:
                login_user(this_user)
                if (role!="admin" and this_user.is_blacklisted):
                    return "You are blacklisted. Contact admin for more details."
            
          
                if role == "admin":
                    return redirect("/admin")
                elif role == "student":
                    session["student_id"] = this_user.id
                    return redirect(f"/student/{this_user.id}")
                elif role == "company":
                    if this_user.is_approved:
                        return redirect(f"/company/{this_user.id}")
                    else:
                        return "Wait for admin approval"
            else:
                return render_template("incorrect_p.html")
        else:
            return render_template("not_exist.html")
    return render_template("login.html")
  
@app.route("/register", methods=['GET', 'POST'])
def register():
  
    if request.method == "POST":
    
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        role = request.form.get("role")

        if not email or not password or not name or not role:
            return "All fields required"

        if len(password) < 3:
            return render_template("register.html", error="Password too short")
        
        



        if role == "student":
            email_exist = Student.query.filter_by(email=email).first()
            
        elif role == "company":
            email_exist = Company.query.filter_by(email=email).first()
        
        
        if email_exist:
            return render_template("already.html")
        else:
            if role == "student":
                new_user = Student(name=name, email=email, password=password, department="", resume_link="", is_blacklisted=False)
            elif role == "company":
                new_user = Company(name=name, email=email, password=password, is_approved=False, is_blacklisted=False, location="")
              
            db.session.add(new_user)
            db.session.commit()

        return redirect("/login")
    
        
    return render_template("register.html")

@app.route("/admin", methods=['GET'])
@login_required 
def admin():
    if not isinstance(current_user, Admin):
        return "Access denied"
  
    this_user = Admin.query.filter_by(id=1).first()
    r_company = Company.query.filter_by(is_approved=True, is_blacklisted=False).all()
    pending_companies = Company.query.filter_by(is_approved=False, is_blacklisted=False).all() 
    students = Student.query.filter_by(is_blacklisted=False).all()
    drives= Drive.query.join(Company).filter(Company.is_blacklisted == False, Company.is_approved == True).all()
    ongoing_drives = Drive.query.join(Company).filter(
    Company.is_blacklisted == False,
    Company.is_approved == True,
    Drive.application_deadline >= db.func.current_date()).all()

    for drive in ongoing_drives:
        if drive.is_rejected:
            drive.status = "Rejected"
        elif drive.is_completed:
            drive.status = "Completed"
        else:
            drive.status = "Ongoing"

    final_ongoing_drives = [drive for drive in ongoing_drives if not drive.is_rejected and not drive.is_completed]

    applications = Application.query.all()
    shortlisted_count = Application.query.filter_by(status="shortlist").count()
    waiting_count = Application.query.filter_by(status="waiting").count()
    rejected_count = Application.query.filter_by(status="reject").count()
    shortlisted_apps = Application.query.filter_by(status="shortlist").all()
    rejected_apps = Application.query.filter_by(status="reject").all()
    total_drives = Drive.query.count()
    total_apps = Application.query.count()
    placements = Application.query.filter_by(status="shortlist").count()
    return render_template("admin_dashboard.html", pending_companies=pending_companies, this_user=this_user, r_company=r_company, students=students, final_ongoing_drives=final_ongoing_drives,drives=drives,  applications=applications,shortlisted_count=shortlisted_count, waiting_count=waiting_count, rejected_count=rejected_count, shortlisted_apps=shortlisted_apps, rejected_apps=rejected_apps, total_drives=total_drives, total_apps=total_apps, placements=placements)

@app.route("/student/<int:student_id>")
@login_required 
def student(student_id):
    
    
    
    if not isinstance(current_user, Student):
        return "Access denied"
    
    if current_user.id != student_id:
        return "Unauthorized access"
    student= current_user
    session["student_id"] = student.id  
    companies=Company.query.filter_by(is_approved=True, is_blacklisted=False).all()
    shortlist = Application.query.filter_by(student_id=student.id, status="shortlist").count()
    reject = Application.query.filter_by(student_id=student.id, status="reject").count()
    waiting = Application.query.filter_by(student_id=student.id, status="waiting").count()
    return render_template("student_dashboard.html", student=student, companies=companies, shortlist=shortlist, reject=reject, waiting=waiting)

@app.route("/company/<int:company_id>")
@login_required 
def company(company_id): 
    session["company_id"] = company_id   
    if not isinstance(current_user, Company):
        return "Access denied"

    if current_user.id != company_id:
        return "Unauthorized access"
    company = Company.query.get(company_id)
    company_drives = Drive.query.filter_by(company_id=company_id).all()
    if company_drives:
        for drive in company_drives:
            if drive.is_rejected:
                drive.status = "Rejected"
            elif drive.is_completed:
                drive.status = "Completed"
            else:
                drive.status = "Ongoing"
    labels = [d.job_title for d in company.drives]
    data = [len(d.applications) for d in company.drives]            
    return render_template("company_dashboard.html", company=company, company_drives=company_drives, labels=labels, data=data)

@app.route("/approve/company/<int:company_id>")
@login_required
def approve(company_id):
    this_company=Company.query.filter_by(id=company_id).first()
    if this_company:
        this_company.is_approved = True
        db.session.commit()
    return redirect("/admin")

@app.route("/blacklist/company/<int:company_id>")
@login_required
def blacklist_comp(company_id):  
    this_company=Company.query.filter_by(id=company_id).first()
    if this_company:
        this_company.is_blacklisted = True
        db.session.commit()
    return redirect("/admin")

@app.route("/blacklist/student/<int:student_id>")
@login_required
def blacklist_stud(student_id):  
    this_student=Student.query.filter_by(id=student_id).first()
    if this_student:
        this_student.is_blacklisted = True
        db.session.commit()
    return redirect("/admin")



@app.route("/reject/drive/<int:drive_id>")
@login_required
def reject(drive_id):
    drive = Drive.query.filter_by(id=drive_id).first()
    if drive:
        drive.is_rejected = True
        db.session.commit()
    return redirect("/admin")

@app.route("/admincomplete/drive/<int:drive_id>")
@login_required
def complete_drive_a(drive_id):
    drive = Drive.query.filter_by(id=drive_id).first()
    if drive:
        drive.completed_on = datetime.now().date()
        drive.is_completed = True
        db.session.commit() 
    return redirect("/admin")   

@app.route("/companycomplete/drive/<int:drive_id>")
@login_required
def complete_drive_c(drive_id):
    drive = Drive.query.filter_by(id=drive_id).first()
    if drive:
        drive.completed_on = datetime.now().date()
        drive.is_completed = True
        db.session.commit() 
    return redirect("/company/{}".format(drive.company_id))    

@app.route("/drive_details_admin/drive/<int:drive_id>")
@login_required
def drive_details_admin(drive_id):
    drive = Drive.query.get(drive_id)
    return render_template("drive_details_admin_dash.html", drive=drive)

@app.route("/drive_details_stud/drive/<int:drive_id>")
@login_required
def drive_details_stud(drive_id):
    drive = Drive.query.get(drive_id)
    student = Student.query.get(session.get("student_id"))
    return render_template("drive_details_student_dash.html", drive=drive, student=student)


@app.route("/search")
def search():
    query = request.args.get('query','').strip()

    this_user = Admin.query.filter_by(id=1).first()
    ongoing_drives = Drive.query.filter(Drive.application_deadline >= db.func.current_date()).all()

    if query:
        students = Student.query.filter((Student.name.ilike(f'%{query}%')) | (Student.id.like(f'%{query}%'))).all()

        r_company = Company.query.filter(Company.is_approved==True,Company.is_blacklisted==False,Company.name.ilike(f'%{query}%')).all()

        pending_companies = Company.query.filter(Company.is_approved==False,Company.is_blacklisted==False,Company.name.ilike(f'%{query}%')).all()

        applications = Application.query.join(Student).join(Drive).join(Company).filter(
            (Student.name.ilike(f'%{query}%')) |
            (Drive.job_title.ilike(f'%{query}%')) |
            (Company.name.ilike(f'%{query}%'))
        ).all()
    else:
        students = Student.query.filter_by(is_blacklisted=False).all()
        r_company = Company.query.filter_by(is_approved=True,is_blacklisted=False).all()
        pending_companies = Company.query.filter_by(is_approved=False,is_blacklisted=False).all()
        applications = Application.query.all()

    shortlisted_apps = [app for app in applications if app.status=="shortlist"]
    rejected_apps = [app for app in applications if app.status=="reject"]
    waiting_apps = [app for app in applications if app.status=="waiting"]

    shortlisted_count = len(shortlisted_apps)
    rejected_count = len(rejected_apps)
    waiting_count = len(waiting_apps)

    total_apps = len(applications)
    total_drives = len(set(app.drive.id for app in applications))
    placements = shortlisted_count

    return render_template("admin_dashboard.html",
        r_company=r_company,
        pending_companies=pending_companies,
        this_user=this_user,
        ongoing_drives=ongoing_drives,
        applications=applications,
        students=students,
        shortlisted_apps=shortlisted_apps,
        rejected_apps=rejected_apps,
        shortlisted_count=shortlisted_count,
        rejected_count=rejected_count,
        waiting_count=waiting_count,
        total_apps=total_apps,
        total_drives=total_drives,
        placements=placements
    )

@app.route("/student_search")
def student_search():
    query = request.args.get("query", "").strip()
    student_id = session.get("student_id")
    student = Student.query.get(student_id)

    if not student:
        return "Unauthorized", 403

    if query:
        drives = Drive.query.join(Company).filter(Company.is_approved == True, Company.is_blacklisted == False, (Drive.job_title.ilike(f"%{query}%")) | (Company.name.ilike(f"%{query}%"))).all()

      
        companies = Company.query.filter(Company.is_approved == True, Company.is_blacklisted == False, Company.name.ilike(f"%{query}%")).all()

    else:
        drives = Drive.query.join(Company).filter(Company.is_approved == True,Company.is_blacklisted == False).all()
        companies = Company.query.filter_by(is_approved=True,is_blacklisted=False).all()

    return render_template("student_dashboard.html", student=student,drives=drives,companies=companies)

@app.route("/create_drive/company/<int:company_id>", methods=['GET', 'POST'])
@login_required
def create_drive(company_id):
    company = Company.query.get(company_id) 
    if request.method == 'POST':
        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        eligibility_criteria = request.form.get("eligibility")
        
        deadline_str = request.form.get("deadline") 
        salary = request.form.get("salary")
        application_deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        if application_deadline < datetime.now().date():
            return render_template("create_drive.html", company_id=company_id, company=company, error="Deadline cannot be in the past")

        if not job_title or not job_description or not eligibility_criteria or not deadline_str or not salary:
            return render_template("create_drive.html", company_id=company_id, company=company, error="All fields required")
        new_drive = Drive(company_id=company_id,job_title=job_title,job_description=job_description,eligibility_criteria=eligibility_criteria,application_deadline=application_deadline,salary=salary, status='Pending', is_rejected=False, is_completed=False)

        db.session.add(new_drive)
        db.session.commit()

        return redirect(f"/company/{company_id}")

    return render_template("create_drive.html", company_id=company_id, company=company)

@app.route("/update_drive/drive/<int:drive_id>", methods=['GET', 'POST'])
@login_required
def update_drive(drive_id):
    drive = Drive.query.get(drive_id)
    if request.method == 'POST':
        

        drive.job_title = request.form.get("job_title") or drive.job_title
        drive.job_description = request.form.get("job_description") or drive.job_description
        drive.eligibility_criteria = request.form.get("eligibility_criteria") or drive.eligibility_criteria
        drive.salary = request.form.get("salary") or drive.salary

       
        deadline_str = request.form.get("application_deadline")

        if deadline_str:
            try:
                drive.application_deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            except ValueError:
                pass  

        db.session.commit()

        return redirect(f"/company/{drive.company_id}")

    return render_template("update_drive.html", drive=drive)


@app.route("/update_app_for_drive/drive/<int:drive_id>")
@login_required
def update_app_for_drive(drive_id):
    drive = Drive.query.get(drive_id)
    applications = Application.query.filter_by(drive_id=drive_id).all()

    return render_template("update_app_for_drive.html",drive=drive,applications=applications)

@app.route("/student_application/<string:student_name>/<int:student_id>/Drive/<int:drive_id>")
@login_required
def student_application(student_name, student_id, drive_id):
    drive=Drive.query.get(drive_id)
    student = Student.query.get(student_id)
   
    applications = Application.query.filter_by(student_id=student_id, drive_id=drive.id).all()
    return render_template("student_application.html", student=student, applications=applications,  drive=drive, student_name=student_name)

@app.route("/edit_profile/student/<int:student_id>", methods=['GET', 'POST'])
@login_required
def update_profile(student_id):
    student = Student.query.get(student_id)

    if request.method == 'POST':
        student.name = request.form.get("name") or student.name
        student.department = request.form.get("department") or student.department
        student.resume_link = request.form.get("resume_link") or student.resume_link
        student.password = request.form.get("password") or student.password

        if not student.name or not student.department or not student.password or not student.resume_link:
            return render_template("student_profile.html", student=student, error="All fields required")

        db.session.commit()

        return redirect(f"/student/{student_id}")

    return render_template("student_profile.html", student=student)


@app.route("/student_app_history/student/<int:student_id>")
@login_required
def student_app_history(student_id):
  
     
    student = Student.query.get(student_id)
    session["student_id"] = student.id 
    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template("student_app_history.html", student=student, applications=applications)

@app.route("/company_details/company/<int:company_id>")
@login_required
def company_details(company_id):
    student = Student.query.get(session.get("student_id"))
    company=Company.query.filter_by(id=company_id, is_approved=True, is_blacklisted=False).first()
    drives=Drive.query.filter_by(company_id=company_id).filter_by(is_rejected=False, is_completed=False).all()
    return render_template("company_details.html", company=company, drives=drives, student=student)




@app.route("/drive_details/drive/<int:drive_id>/company/<int:company_id>")
@login_required
def drive_details_company(drive_id, company_id):
    student = Student.query.get(session.get("student_id"))
    drive = Drive.query.get(drive_id)
    company = Company.query.get(company_id)
    return render_template("student_drive_apply.html", drive=drive, company=company, student=student)


@app.route("/apply/drive/<int:drive_id>/student/<int:student_id>")
@login_required
def apply_drive(drive_id, student_id):
    drive = Drive.query.get(drive_id)
    student = Student.query.get(session.get("student_id"))

    if drive and student:
        existing_application = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
        if existing_application:
            return "You have already applied for this drive."
        
        new_application = Application(student_id=student_id, drive_id=drive_id, application_date=datetime.now().date(), status='Applied')
        db.session.add(new_application)
        db.session.commit()
        return redirect(f"/student/{student_id}")
    else:
        return "Invalid drive or student."

@app.route("/student_application_company/<string:student_name>/<int:student_id>/Drive/<int:drive_id>")
@login_required
def student_application_company(student_name, student_id, drive_id):
    student = Student.query.get(session.get("student_id"))
    drive = Drive.query.get(drive_id)
    applications = Application.query.filter_by(student_id=student_id, drive=drive).all()
    return render_template("student_application_company.html", student=student, applications=applications, student_name=student_name)


@app.route("/update_status/application/<int:application_id>" , methods=['POST'])
@login_required
def update_app_status(application_id):
    new_status = request.form.get("status")
    application = Application.query.get(application_id)
    if application:
        application.status = new_status
        db.session.commit()
        return redirect(f"/update_app_for_drive/drive/{application.drive_id}")
    else:
        return "Application not found."



@app.route("/logout")
def logout():
    logout_user() 
    return redirect("/login")
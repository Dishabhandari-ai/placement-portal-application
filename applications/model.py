from .database import db
from flask_login import UserMixin

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Student(db.Model, UserMixin):
    __tablename__ = 'student'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    resume_link = db.Column(db.String(255), nullable=True)
    drives = db.relationship('Drive',secondary='application',back_populates='students', viewonly=True)
    applications = db.relationship('Application', backref='student')
    is_blacklisted = db.Column(db.Boolean(), default=False, nullable=False)


class Company(db.Model, UserMixin):
    __tablename__ = 'company'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_approved = db.Column(db.Boolean(), default=False, nullable=False)
    is_blacklisted = db.Column(db.Boolean(), default=False, nullable=False)
    drives = db.relationship('Drive', backref='company')
    location = db.Column(db.String(255), nullable=False)
    


class Drive(db.Model):
    __tablename__ = 'drive'
    id = db.Column(db.Integer(), primary_key=True)
    students=db.relationship('Student',secondary='application',back_populates='drives', viewonly=True)
    company_id = db.Column(db.Integer(), db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.String(255), nullable=False)
    eligibility_criteria = db.Column(db.String(255), nullable=False)
    application_deadline = db.Column(db.Date(), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    salary = db.Column(db.String(50), nullable=False)
    is_rejected = db.Column(db.Boolean(), default=False, nullable=False)
    is_completed = db.Column(db.Boolean(), default=False, nullable=False)
    completed_on = db.Column(db.Date(), nullable=True)
    applications = db.relationship('Application', backref='drive')


class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Integer(), db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer(), db.ForeignKey('drive.id'), nullable=False)
    application_date = db.Column(db.Date(), nullable=False)
    status = db.Column(db.String(50), default='Applied')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_application'),
    )
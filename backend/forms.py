from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, RadioField, DateField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from models import User

class CustomerRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=11, max=11)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    age = IntegerField('Age', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_phone_number(self, phone_number):
        if not phone_number.data.isdigit() or len(phone_number.data) != 11:
            raise ValidationError('Phone number must be exactly 11 digits.')
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('That phone number is already registered. Please login.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    login_type = RadioField('Login As', choices=[('customer', 'Customer'), ('staff', 'Staff'), ('admin', 'Admin')], default='customer', validators=[DataRequired()])
    email = StringField('Email (Customer/Admin)')
    staff_id = StringField('Staff ID (Staff)')
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

    def validate(self, extra_validators=None):
        if not FlaskForm.validate(self, extra_validators):
            return False
        
        if self.login_type.data in ['customer', 'admin']:
            if not self.email.data:
                self.email.errors.append('Email is required for Customer and Admin Login.')
                return False
        elif self.login_type.data == 'staff':
            if not self.staff_id.data:
                self.staff_id.errors.append('Staff ID is required for Staff Login.')
                return False
        return True

class FlightSearchForm(FlaskForm):
    # Optional() prevents crash on GET when date is empty
    date = DateField('Departure Date', format='%Y-%m-%d', validators=[Optional()])
    origin = StringField('Origin', validators=[DataRequired()])
    destination = StringField('Destination', validators=[DataRequired()])
    trip_type = SelectField('Trip Type', choices=[('one_way', 'One Way'), ('return', 'Return')], default='one_way')
    adults = SelectField('Adults', choices=[(str(i), str(i)) for i in range(1, 10)], default='1')
    children = SelectField('Children', choices=[(str(i), str(i)) for i in range(0, 10)], default='0')
    infants = SelectField('Infants', choices=[(str(i), str(i)) for i in range(0, 5)], default='0')
    submit = SubmitField('Search Flights')

class PackageSelectionForm(FlaskForm):
    package_tier = RadioField('Select Package', choices=[('Economy', 'Economy (Green)'), ('Basic', 'Basic (Blue)'), ('Premium', 'Premium (Gold)')], validators=[DataRequired()])
    submit = SubmitField('Continue to Passenger Details')

class PassengerForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    seat_number = StringField('Seat Number', validators=[DataRequired()])
    meal_preference = RadioField('Meal Preference', choices=[('None', 'None'), ('Vegetarian', 'Vegetarian'), ('Non-Vegetarian', 'Non-Vegetarian')], default='None')

class PassengerDetailsForm(FlaskForm):
    passengers_count = IntegerField('Number of Passengers', validators=[DataRequired()], default=1)
    # The actual passenger subforms will be rendered manually in the template for simplicity
    submit = SubmitField('Proceed to Final Checkout')

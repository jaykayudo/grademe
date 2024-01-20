
# GradeMe

A result checking and uploading web application for students and academic staffs in tertiary instutions.


## Run Locally

Clone the project

```bash
  git clone https://github.com/jaykayudo/grademe.git
```

Go to the project directory

```bash
  cd grademe
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Start the server

```bash
  python manage.py runserver
```


## Credentials
### Note: this credentials is for the test database

```bash
Chief Admin
email: chiefadmin@gmail.com
password: chiefadmin

Admin
email: admin@gmail.com
password: admin

Student
email: student@gmail.com (passwordless sign in)
```
## Features

- Notification
- Email Verification for login
- Result Upload from csv file
- Result Upload from excel file
- Result Upload from form data
- Asynchoronous task with celery for bulk result Upload
- Dynamic form for singles result Upload
- Downloading Result data to pdf file
- Geolocation for Login Notification and Tracking
- Device Tracking
- Actions to Keep track of all actions performed by admins
- Auth Feautures: Reset Password for Chiefadmin, Change Password, Change Email





---
## :hammer_and_wrench: Languages and Tools:

<div>
 <img src="https://github.com/devicons/devicon/blob/master/icons/html5/html5-original.svg" title="HTML5" alt="HTML" width="40" height="40"/>&nbsp;
 <img src="https://github.com/devicons/devicon/blob/master/icons/css3/css3-plain-wordmark.svg"  title="CSS3" alt="CSS" width="40" height="40"/>&nbsp;
 <img src="https://github.com/devicons/devicon/blob/master/icons/bootstrap/bootstrap-original.svg"  title="Bootstrap" alt="Bootstrap" width="40" height="40"/>&nbsp;

 <img src="https://github.com/devicons/devicon/blob/master/icons/javascript/javascript-original.svg" title="JavaScript" alt="JavaScript" width="40" height="40"/>&nbsp;
 <img src="https://github.com/devicons/devicon/blob/master/icons/python/python-original-wordmark.svg" title="Python" alt="Python" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/django/django-plain-wordmark.svg" title="Django" alt="Django" width="40" />&nbsp;
</div>
---
## Third Party Packages
- Django Role Permission: for a more enhanced way of managing permissions
- Django User agents: for user's device information
- Geoip2 - for user location 
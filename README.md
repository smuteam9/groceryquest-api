## Setup
  
Requirements for development environment:  

Python 3  
pip  
virtualenv  
autoenv (optional)  
PostgreSQL  

## virtualenv setup

1. Create a virtualenv titled "groceryquest" in project directory:  
`virtualenv groceryquest`  

2. Make .env executable:  
`chmod +x .env`  

3. Activate the virtualenv by either of the following:  
`cd ../<project directory>`  
`source groceryquest/bin/activate`  

4. Install dependencies:  
`pip install -r requirements.txt`
  

## Database setup  

Make sure PostgreSQL is installed and that your user has a role, and that you have created a database called "groceryquest", then  

`python manage.py db init`  
`python manage.py db migrate`  
`python manage.py db upgrade`  

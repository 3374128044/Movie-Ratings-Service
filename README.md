# Movie-Ratings-Service

**Team members**: Samuel Luong, Deborah Shaw, Qing Gao, Jose Diaz
## Instruction
The movie rating servers is an API allows users to sign up, login, and submit rating for movies. Admins can manage movies in the database but are not allowed to submit ratings. JWT authentication ensures secure login and authorization. The service includes features such as adding, updating, retrieving, and deleting movie ratings. Additionally, an API for file uploads supports specific file extensions only.

## Setup and installation
### Prerequisites
- **Python 3**
- **pip**
- **Flask**

1. clone the repository: 
```bash
git clone https://github.com/3374128044/Movie-Ratings-Service.git
```
```bash
cd Movie-Ratings-Service
```

2. Set up virtual environment
```bash
virtualenv venv
source venv/bin/activate
```

3. Run the Flask app
```bash
python movie-rating-service.py
```
 or 
```bash
python fileUpload.py
```


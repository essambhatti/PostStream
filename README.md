Poststream — Flask Social Media App
===================================

**Poststream** is a feature-rich social media app built with Flask. It includes user authentication, email verification, real-time private chat, hashtag-based trend tracking, and AI-powered content moderation using web-based public APIs. The app uses SQLite as its lightweight database and is fully dockerized for easy setup and deployment.

Tech Stack
----------

*   Python + Flask
    
*   SQLite (lightweight local database)
    
*   Flask-SocketIO for real-time chat
    
*   NudeNet (via web-based API) for content moderation
    
*   Transformers (HuggingFace) for AI/NLP tasks
    
*   SMTP (smtplib) for email verification
    
*   Bootstrap (dark theme) for frontend styling
    
*   Docker for containerization
    

Features
--------

*   User registration and login with email verification
    
*   Upload and share text, image, and video posts
    
*   Automatic AI moderation using public APIs (NudeNet, Transformers)
    
*   Real-time chat powered by Flask-SocketIO
    
*   Trending topics via hashtag tracking (many-to-many with posts)
    
*   Responsive UI with a clean dark Bootstrap theme
    
*   Dockerized for easy setup and cross-platform compatibility
    

How to Run Locally (Without Docker)
-----------------------------------

1.  **Clone the Repository**git clone https://github.com/your-username/poststream.git
    
2.  **Navigate to the Directory**cd poststream
    
3.  **Create a Virtual Environment and Activate It**
    
    *   macOS/Linux:python -m venv venv && source venv/bin/activate
        
    *   Windows:python -m venv venv && venv\\Scripts\\activate
        
4.  **Install Dependencies**pip install -r requirements.txt
    

SECRET\_KEY=your\_secret\_keyMAIL\_SERVER=smtp.gmail.comMAIL\_PORT=587MAIL\_USERNAME=your\_emailMAIL\_PASSWORD=your\_email\_password

1.  **Run the Application**python run.pyVisit http://localhost:5000 in your browser.
    

How to Run with Docker
----------------------

1.  bashCopyEditdocker build -t poststream .
    
2.  bashCopyEditdocker run -d -p 5000:5000 --env-file .env poststream
    
3.  Visit http://localhost:5000 in your browser.
    

> Make sure your .env file is in the root directory before running the container.

License
-------

This project is licensed under the MIT License.

Author
------

**Essam Bhatti**
\Feel free to contribute or open issues with suggestions and feedback.

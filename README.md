# 🥛 LushDairy - E-Commerce Website

LushDairy is a full-stack **Django-based e-commerce platform** focused on dairy products.  
It provides a seamless shopping experience with features for **customers and admins**.

---

## 🚀 Features

### 👤 User
- Register/Login with OTP and social authentication
- Browse products with filters, sorting & pagination
- Add to cart, wishlist, and manage multiple addresses
- Checkout with Razorpay payment gateway
- View/cancel orders, download invoices
- Profile management with order history and wallet



### 🔑 Admin
- Manage users,products,categories,offers,coupons,wallet,complaints,stocks and variants
- manage sales report,download in pdf and excel form
- Approve/reject complaints for refund management
- order management,update status,order detail
- Manage categories & subcategories
- Dashboard with analytics (future scope)

---

## 🛠️ Tech Stack

- **Backend:** Django (MVT architecture)
- **Frontend:** HTML, CSS, Bootstrap, JS, AJAX
- **Database:** PostgreSQL 
- **Authentication:** Django sessions + OTP + social login
- **Payments:** Razorpay integration
- **Deployment:**AWS / Nginx + Gunicorn
- **Version Control:** Git & GitHub

---

## 📂 Project Structure
lushdairy/
│── manage.py             #Django’s command-line utility (runserver, makemigrations, createsuperuser)
│── requirements.txt      #List of all dependencies (pip freeze > requirements.txt).
│── README.md             #Documentation file for GitHub/others.
│──.gitignore             #Tells Git which files/folders to ignore (like venv/, __pycache__/, .env).
│
├── accounts/             #admin related features
│   │── __init__.py
│   │── models.py         #models related to accounts 
│   │── forms.py          #forms related to accounts 
│   │── views.py          #views related to accounts 
│   │── urls.py           #Routes for authentication
│   │── signals.py        #admin side signals
│   │── admin.py          #Admin panel setup for account models
│   │── tests.py    
├── app/                  #user side features
│   │── __init__.py
│   │── models.py         #User related models
│   │── forms.py          #Signup/Login forms (with OTP/email validation)
│   │── views.py          #user related all views
│   │── urls.py           #Routes for authentication
│   │── signals.py        #User signals
│   │── admin.py          #User side configurations
│   │── tests.py
│   │── middleware.py     #Custom middlewares (eg:prevent access of normal user on admin side)
│   │── utils.py          #Helper functions
│
├── LushDairy ├──.env     # Environment variables (SECRET_KEY, DB credentials, API keys)
│             ├──asgi.py  # Entry point for async servers
│             ├──wsgi.py  # Entry point for deployment servers (Gunicorn, uWSGI)
│             ├──urls.py  # Root URL router (includes all apps’ URLs)
│             ├──settings.py  # Django settings (DB, static, installed apps, etc.)
│  
│               
├── media/                # stores media files
├── static/               # stores static files
└── templates/ ├──admin_panel  # admin related html files
               ├──user_panel   # user related html files





---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/lushdairy.git
   cd lushdairy
2. **Create virtual environment**

    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate


3. **Install dependencies**

    pip install -r requirements.txt


4. **setip environment variables (.env)**

    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=127.0.0.1, localhost
    EMAIL_HOST_USER=your_email
    EMAIL_HOST_PASSWORD=your_email_password
    RAZORPAY_KEY=your_razorpay_key
    RAZORPAY_SECRET=your_razorpay_secret


5. **Run migrations**

    python manage.py makemigrations
    python manage.py migrate


6. **Create superuser**

    python manage.py createsuperuser

7. **Run server**

    python manage.py runserver



📜 License

This project is licensed under the MIT License.

🤝 Contributing

Contributions are welcome!

Fork the repo

Create a feature branch (git checkout -b feature-name)

Commit changes (git commit -m 'Add feature')

Push to branch (git push origin feature-name)

Open a Pull Request

👨‍💻 Author

Binzy Mol K
📧 jazbinzy@gmail.com
🔗 https://github.com/Binzyjazeel


---


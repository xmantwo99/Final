# Final

Cherry Keyboards Web App
Final Project for CS188
Contributors: Xavier Washington, Garrett Provence, Anthony Sneddon, Sean Chen

📋 Overview
Cherry Keyboards is a full-stack web application that allows users to browse, customize, and purchase high-quality mechanical keyboards. Users can log in, register, build their own custom keyboards, manage their shopping cart, and complete secure checkouts. The project is built with Flask and uses Microsoft Azure SQL for database management.

🚀 Features
🔒 User Authentication (Username/Password & Google OAuth)

🛒 Cart & Checkout System

🎨 Custom Keyboard Builder (choose switches, layout, case)

🧾 Order Confirmation with Tracking Info

📷 Product Listings with Images and Descriptions

✅ Frontend + Backend Automated Testing

🏗️ Architecture
Presentation Layer:

HTML templated with Jinja2

CSS, images, and static files served via /static

Application Layer (Flask):

Handles routing, session management, and request validation

Flask Blueprints used to manage authentication and builder modules

Data Layer:

User and Product ORM models connected to Azure SQL

Session-based cart stored securely on the client side

📄 Key Endpoints
Method	Route	Description
GET	/	Landing page
GET	/products	View product listings
GET	/add_to_cart/<product_id>	Add item to cart
GET	/add_custom_build	Add custom build to cart
GET	/remove_from_cart/<product_id>	Remove item from cart
GET	/cart	View shopping cart
GET	/checkout	Checkout and confirm order
GET/POST	/login	Log in with account
GET/POST	/signup	Register a new account
GET	/logout	Logout and clear session
GET	/builder	Open custom keyboard builder
POST	/builder_preview	Preview custom build
GET	/add-sample-products	Populate sample products (admin only)

🧪 Frontend Testing
All frontend functionality was tested manually and passed the following cases:

User login/signup, including error handling and field validation

Add to cart / Remove from cart

Create custom build and preview

View cart summary

Checkout process with confirmation

Google OAuth login and signup

🧪 Backend Testing
Automated unit tests were created to validate backend logic and are documented here.

💡 Technologies Used
Flask – Web framework and routing

Flask-Login – User session management

Werkzeug Security – Password hashing and verification

pyodbc + ODBC Driver 18 – Database connection to Azure SQL

Microsoft Azure SQL Database – Scalable database backend

Jinja2 Templates – HTML rendering engine

Google OAuth 2.0 – Google login/signup support

👨‍💻 Team Contributions
Member	Contributions
Xavier	Backend development, database integration
Anthony	Backend development, SQL integration
Garrett	Frontend UI/UX, component design
Sean	Frontend logic, layout styling

The team worked collaboratively, with crossover between backend and frontend as needed to maintain coherence across features.

🛠️ Future Improvements
Implement 3D hand measurement tool for custom-fit split keyboards

Add visual mockups for custom builds

Order history and profile pages

Stripe or PayPal integration for real transactions

📷 Screenshots
To be added – Figma mockups and live demo screenshots

📦 Setup & Deployment
Clone the repository

Set up a virtual environment and install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Configure .env file with your Azure SQL credentials and Google OAuth secrets

Run the Flask server:

bash
Copy
Edit
uv run dev run
📬 Contact
For questions or contributions, reach out to any of the project members or open an issue in the repository.
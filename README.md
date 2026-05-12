# Lost and Found Management System For Collage

## Overview
The Lost and Found Management System is a web application designed to help users report lost or found items. It allows users to register using their college email, log in, report items, and manage their profile. The system sends OTPs for email verification and password recovery. 

## Functionalities
- **User Registration:** Users can register using their college email and verify it with an OTP sent to their inbox.
- **User Login & Logout:** Registered users can log in to the system, and they can also log out securely.
- **Password Reset:** Users can reset their password using an OTP sent to their registered email.
- **Lost & Found Item Management:** Users can report items they have lost or found, view a list of items, and filter them based on categories or search terms.

## Technologies Used
- **Backend:** Flask, Flask-Bcrypt (for password hashing), Flask-Login (for user sessions), Flask-Mail (for sending OTP emails).
- **Database:** MySQL (used via SQLAlchemy ORM).
- **Frontend:** HTML, CSS, JavaScript (for dynamic interactions).
- **Authentication:** Secure email-based OTP verification and password reset mechanism.
- **Security:** Bcrypt for password hashing, Flask-Login for session management, and secure file uploads.

## Future Enhancements
- **Item Matching:** Automatically match found items with reported lost items.
- **User Notifications:** Notify users when their item status changes.

## License
This project is licensed under the MIT License. you are welcome to enhance the application.

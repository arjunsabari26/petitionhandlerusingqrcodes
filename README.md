# Petition Handler Using QR Codes 📱

A full-stack, responsive web application for managing petitions, complaints, and service requests. The system uses dynamically generated QR codes that mobile users can scan to instantly open a pre-filled submission form.

## Technology Stack 🛠️
- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Frontend:** HTML5, CSS3, Bootstrap 5, FontAwesome
- **Database:** SQLite
- **QR Code Generation:** qrcode, Pillow

## Features ✨
### For General Users
- **Mobile-Friendly Submission:** Scan a location-specific QR code to submit a query instantly.
- **Live Status Tracking:** Use an 8-character ID to track petition progress (Submitted → In Review → Processing → Resolved).
- **User Dashboard:** Register an account to view and manage all your past and active petitions in one place.
- **Notifications:** Dashboard alerts inform you when an admin updates the status or provides a resolution.

### For Administrators
- **Dynamic QR Code Generation:** Generate specialized QR codes for different query types (e.g., "Maintenance", "IT Support"). *QR Codes use your computer's local IP address so they are directly scannable by mobile phones on the same WiFi network!*
- **Petition Management Console:** View all incoming petitions, complete with user details and descriptions.
- **Status Updates & Responses:** Update the progress of petitions and send official resolutions or replies directly to the user's dashboard timeline.
- **Analytics Overview:** See high-level metrics of resolved vs pending petitions on the admin panel.

## Instructions to Run 🚀

### 1. Setup Environment
Ensure you have Python installed. The project runs on Python 3.
Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

### 2. Start the Server
Run the Flask application:

```bash
python app.py
```
*Note: The application automatically binds to `0.0.0.0:5000` to allow other devices on your network to access it.*

### 3. Create an Admin Account
1. Open your browser and go to `http://localhost:5000`
2. Click **Sign Up**.
3. Register using any email address ending in **`@admin.com`** (For example: `boss@admin.com`). The application will automatically grant this account Administrative privileges.

### 4. How to Test QR Codes with a Phone 📱
1. Make sure your Phone and Computer are connected to the **same WiFi network**.
2. Log in as an Admin on your computer and navigate to the **Admin Dashboard**.
3. Under *Generate QR Code*, type a category like `Plumbing Issue` and click Generate.
4. The system automatically fetches your computer's local network IP and creates a custom QR code.
5. Open your Phone's Camera, scan the QR code on the screen, and it will direct you seamlessly to the pre-filled submit form on your phone!

## Design Details 🎨
The interface has robust modern, **clean, and vibrant UI** elements built completely with Bootstrap 5 and custom polished CSS containing:
- Glassmorphic card layouts
- Smooth fade-in and transition animations
- Intuitive and responsive progress trackers
- Interactive tooltips and modal dialogs


Developed with clean architecture for high scalability and user interaction.

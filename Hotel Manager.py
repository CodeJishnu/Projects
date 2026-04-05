import mysql.connector
import datetime
import maskpass
import random
import string
from tabulate import tabulate
from rich.console import Console
from rich.text import Text

#To activate the virtual environment, use the following command in your terminal: source venv/bin/activate
#Run this next: python3 "Hotel Manager.py"

# Admin username: admin
# Admin password: admin123

# Create a console object
console = Console()

# Create a text object for the banner
banner_text = Text("""
██╗  ██╗ ██████╗ ████████╗███████╗██╗     
██║  ██║██╔═══██╗╚══██╔══╝██╔════╝██║     
███████║██║   ██║   ██║   █████╗  ██║     
██╔══██║██║   ██║   ██║   ██╔══╝  ██║     
██║  ██║╚██████╔╝   ██║   ███████╗███████╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚══════╝
                                          
███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
""", style="bold cyan")

# Database Connection Details
# Change these values to match your local MySQL configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root@123',  # Change this to your MySQL password
}

def establish_connection():
    try:
        mydb = mysql.connector.connect(**DB_CONFIG)
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS Hotel_Manager")
        mycursor.execute("USE Hotel_Manager")
        
        # Creating tables
        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS Rooms (
                room_id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(10) UNIQUE,
                type VARCHAR(20),
                price_per_night DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'Available'
            )
        """)
        
        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS Guests (
                guest_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50),
                phone VARCHAR(15),
                email VARCHAR(50)
            )
        """)
        
        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS Bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT,
                guest_id INT,
                check_in DATE,
                check_out DATE,
                total_amount DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'Booked',
                FOREIGN KEY (room_id) REFERENCES Rooms(room_id),
                FOREIGN KEY (guest_id) REFERENCES Guests(guest_id)
            )
        """)
        
        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS Admin_Login (
                user VARCHAR(25) PRIMARY KEY, 
                password VARCHAR(25)
            )
        """)
        
        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id VARCHAR(25) PRIMARY KEY,
                password VARCHAR(25) NOT NULL
            )
        """)
        
        # Initial setup
        mycursor.execute("SELECT * FROM Admin_Login")
        if mycursor.fetchone() is None:
            mycursor.execute("INSERT INTO Admin_Login VALUES (%s, %s)", ('admin', 'admin123'))
            
        # Initial rooms if empty
        mycursor.execute("SELECT COUNT(*) FROM Rooms")
        if mycursor.fetchone()[0] == 0:
            rooms_data = [
                ('101', 'Single', 1000.00), ('102', 'Single', 1000.00),
                ('201', 'Double', 2000.00), ('202', 'Double', 2000.00),
                ('301', 'Suite', 5000.00), ('302', 'Suite', 5000.00)
            ]
            mycursor.executemany("INSERT INTO Rooms (room_number, type, price_per_night) VALUES (%s, %s, %s)", rooms_data)
            
        mydb.commit()
        return mydb, mycursor
    except mysql.connector.Error as err:
        console.print(f"[bold red]Error: {err}[/bold red]")
        return None, None

def admin_login(mycursor):
    console.print("\n[bold yellow]--- Admin Login ---[/bold yellow]")
    user = input("Enter Admin Username: ")
    pwd = maskpass.askpass(prompt="Enter Admin Password: ", mask="*")
    mycursor.execute("SELECT * FROM Admin_Login WHERE user = %s AND password = %s", (user, pwd))
    return mycursor.fetchone() is not None

def user_login_menu(mydb, mycursor):
    while True:
        console.print("\n[bold green]--- User Menu ---[/bold green]")
        console.print("1. Login")
        console.print("2. Register")
        console.print("3. Back to Main Menu")
        choice = input("Enter choice: ")
        
        if choice == '1':
            user_id = input("Enter User ID: ")
            pwd = maskpass.askpass(prompt="Enter Password: ", mask="*")
            mycursor.execute("SELECT * FROM Users WHERE user_id = %s AND password = %s", (user_id, pwd))
            if mycursor.fetchone():
                user_dashboard(mydb, mycursor, user_id)
            else:
                console.print("[bold red]Invalid credentials![/bold red]")
        elif choice == '2':
            user_id = input("Create User ID: ")
            pwd = input("Create Password: ")
            try:
                mycursor.execute("INSERT INTO Users VALUES (%s, %s)", (user_id, pwd))
                mydb.commit()
                console.print("[bold green]Registration successful![/bold green]")
            except:
                console.print("[bold red]User ID already exists![/bold red]")
        elif choice == '3':
            break

def admin_dashboard(mydb, mycursor):
    while True:
        console.print("\n[bold cyan]=== Admin Dashboard ===[/bold cyan]")
        console.print("1. View All Rooms")
        console.print("2. View All Guests")
        console.print("3. View All Bookings")
        console.print("4. Add New Room")
        console.print("5. Update Room Status")
        console.print("6. Logout")
        choice = input("Enter choice: ")
        
        try:
            if choice == '1':
                mycursor.execute("SELECT * FROM Rooms")
                data = mycursor.fetchall()
                print(tabulate(data, headers=['ID', 'Number', 'Type', 'Price', 'Status'], tablefmt='grid'))
            elif choice == '2':
                mycursor.execute("SELECT * FROM Guests")
                data = mycursor.fetchall()
                print(tabulate(data, headers=['ID', 'Name', 'Phone', 'Email'], tablefmt='grid'))
            elif choice == '3':
                mycursor.execute("""
                    SELECT b.booking_id, r.room_number, g.name, b.check_in, b.check_out, b.total_amount, b.status 
                    FROM Bookings b 
                    JOIN Rooms r ON b.room_id = r.room_id 
                    JOIN Guests g ON b.guest_id = g.guest_id
                """)
                data = mycursor.fetchall()
                print(tabulate(data, headers=['ID', 'Room', 'Guest', 'In', 'Out', 'Amount', 'Status'], tablefmt='grid'))
            elif choice == '4':
                num = input("Room Number: ")
                rtype = input("Type (Single/Double/Suite): ")
                price = float(input("Price: "))
                mycursor.execute("INSERT INTO Rooms (room_number, type, price_per_night) VALUES (%s, %s, %s)", (num, rtype, price))
                mydb.commit()
                console.print("[bold green]Room added![/bold green]")
            elif choice == '5':
                rid = int(input("Enter Room ID: "))
                stat = input("New Status (Available/Occupied/Maintenance): ")
                mycursor.execute("UPDATE Rooms SET status = %s WHERE room_id = %s", (stat, rid))
                mydb.commit()
                console.print("[bold green]Status updated![/bold green]")
            elif choice == '6':
                break
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

def user_dashboard(mydb, mycursor, user_id):
    while True:
        console.print(f"\n[bold green]=== Welcome {user_id} ===[/bold green]")
        console.print("1. View Available Rooms")
        console.print("2. Book a Room")
        console.print("3. My Bookings")
        console.print("4. Logout")
        choice = input("Enter choice: ")
        
        try:
            if choice == '1':
                mycursor.execute("SELECT room_number, type, price_per_night FROM Rooms WHERE status = 'Available'")
                data = mycursor.fetchall()
                print(tabulate(data, headers=['Number', 'Type', 'Price'], tablefmt='grid'))
            elif choice == '2':
                # Booking logic
                mycursor.execute("SELECT room_id, room_number, type, price_per_night FROM Rooms WHERE status = 'Available'")
                rooms = mycursor.fetchall()
                if not rooms:
                    console.print("[bold red]No rooms available![/bold red]")
                    continue
                
                print(tabulate(rooms, headers=['ID', 'Number', 'Type', 'Price'], tablefmt='grid'))
                rid = int(input("Enter Room ID to book: "))
                
                # Check if valid room
                mycursor.execute("SELECT price_per_night FROM Rooms WHERE room_id = %s AND status = 'Available'", (rid,))
                room_info = mycursor.fetchone()
                if not room_info:
                    console.print("[bold red]Invalid Room ID or Room not available![/bold red]")
                    continue
                
                name = input("Enter Guest Name: ")
                phone = input("Enter Phone: ")
                email = input("Enter Email: ")
                
                cin = input("Check-in Date (YYYY-MM-DD): ")
                cout = input("Check-out Date (YYYY-MM-DD): ")
                
                d1 = datetime.datetime.strptime(cin, "%Y-%m-%d")
                d2 = datetime.datetime.strptime(cout, "%Y-%m-%d")
                days = (d2 - d1).days
                if days <= 0:
                    console.print("[bold red]Invalid dates![/bold red]")
                    continue
                
                total = days * float(room_info[0])
                console.print(f"[bold yellow]Total Amount: {total}[/bold yellow]")
                
                # Payment Simulation
                console.print("\n--- Payment Portal ---")
                card = maskpass.askpass(prompt="Enter Card Number (Simulation): ", mask="*")
                cvv = maskpass.askpass(prompt="Enter CVV: ", mask="*")
                console.print("[bold green]Processing Payment... Success![/bold green]")
                
                # Transaction
                mycursor.execute("INSERT INTO Guests (name, phone, email) VALUES (%s, %s, %s)", (name, phone, email))
                gid = mycursor.lastrowid
                
                mycursor.execute("""
                    INSERT INTO Bookings (room_id, guest_id, check_in, check_out, total_amount, status) 
                    VALUES (%s, %s, %s, %s, %s, 'Booked')
                """, (rid, gid, cin, cout, total))
                
                mycursor.execute("UPDATE Rooms SET status = 'Occupied' WHERE room_id = %s", (rid,))
                mydb.commit()
                console.print("[bold green]Booking Confirmed![/bold green]")
                
            elif choice == '3':
                # This simple version shows all bookings for simplicity, 
                # but in a real app, we'd link Guests to Users
                mycursor.execute("""
                    SELECT b.booking_id, r.room_number, b.check_in, b.check_out, b.status 
                    FROM Bookings b 
                    JOIN Rooms r ON b.room_id = r.room_id
                """)
                data = mycursor.fetchall()
                print(tabulate(data, headers=['ID', 'Room', 'In', 'Out', 'Status'], tablefmt='grid'))
            elif choice == '4':
                break
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

def main():
    mydb, mycursor = establish_connection()
    if not mydb: return

    while True:
        console.print("********************************************************************************")
        console.print(banner_text)
        console.print("********************************************************************************")
        console.print("\n1. Admin Portal")
        console.print("2. User Portal")
        console.print("3. Exit")
        
        choice = input("Select Portal: ")
        
        if choice == '1':
            if admin_login(mycursor):
                admin_dashboard(mydb, mycursor)
            else:
                console.print("[bold red]Access Denied![/bold red]")
        elif choice == '2':
            user_login_menu(mydb, mycursor)
        elif choice == '3':
            console.print("[bold cyan]Thank you for using Hotel Manager![/bold cyan]")
            break
        else:
            console.print("[bold red]Invalid choice![/bold red]")

if __name__ == "__main__":
    main()

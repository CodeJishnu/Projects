import mysql.connector
import maskpass
import datetime  
import wikipediaapi
from tabulate import tabulate
from rich.console import Console
from rich.text import Text
import re
import random
import string
import requests
import feedparser
import ssl 

# Create a console object
console = Console()

# Create a text object for the banner
banner_text = Text("""██████╗  ██████╗  ██████╗ ██╗  ██╗    ███╗   ███╗ █████╗ ████████╗███████╗
██╔══██╗██╔═══██╗██╔═══██╗██║ ██╔╝    ████╗ ████║██╔══██╗╚══██╔══╝██╔════╝
██████╔╝██║   ██║██║   ██║█████╔╝     ██╔████╔██║███████║   ██║   █████╗  
██╔══██╗██║   ██║██║   ██║██╔═██╗     ██║╚██╔╝██║██╔══██║   ██║   ██╔══╝  
██████╔╝╚██████╔╝╚██████╔╝██║  ██╗    ██║ ╚═╝ ██║██║  ██║   ██║   ███████╗
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
                                                                          """)

# Print the banner
print("******************************************************************************************************************************************************************")
print("  ")
console.print(banner_text)
print(' ')
print("******************************************************************************************************************************************************************")
# Establishing the connection
mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root@123'
)
mycursor = mydb.cursor()
print("WELCOME TO BOOKMATE-LIBRARY MANAGER")

# Creating and using the database
mycursor.execute("CREATE DATABASE IF NOT EXISTS Library_Manager")
mycursor.execute("USE Library_Manager")

# Creating tables if they don't exist
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS Available_Books (
        id INT PRIMARY KEY, 
        Name VARCHAR(25), 
        Subject VARCHAR(25), 
        Quantity INT
    )
""")
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS Books_issued (
        id INT PRIMARY KEY, 
        Name VARCHAR(25), 
        Subject VARCHAR(25), 
        S_Name VARCHAR(25), 
        S_Class VARCHAR(25),
        Issue_Date date,
        Status varchar(25)
    )
""")
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS Admin_Login (
        User VARCHAR(25), 
        Password VARCHAR(25)
    )
""")
mycursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    User_ID VARCHAR(25) PRIMARY KEY,
    Password VARCHAR(25) NOT NULL
);
""")
mycursor.execute("""
CREATE TABLE IF NOT EXISTS Available_Ebooks (
    Ebook_ID INT PRIMARY KEY,
    Ebook_Name VARCHAR(25),
    Subject VARCHAR(25)
);
""")

mydb.commit()
#Adding new columns
mycursor.execute("SHOW COLUMNS FROM Books_issued LIKE 'Issue_Date'")
result = mycursor.fetchone()
if not result:
    mycursor.execute("ALTER TABLE Books_issued ADD COLUMN Issue_Date DATE")
    mydb.commit()
mycursor.execute("SHOW COLUMNS FROM Books_issued LIKE 'Status'")
result = mycursor.fetchone()
if not result:
    mycursor.execute("ALTER TABLE Books_issued ADD COLUMN Status VARCHAR(25)")
    mydb.commit()

# Initial admin login setup
mycursor.execute("SELECT * FROM Admin_Login")
if mycursor.fetchone() is None:
    mycursor.execute("INSERT INTO Admin_Login VALUES (%s, %s)", ('Admin', '1234'))
    mydb.commit()

def calculate_fine(days_overdue):
    # Constants
    GRACE_PERIOD = 5  # Days during which no fines are charged
    DAILY_FINE = 2    # Daily fine after grace period
    MAX_FINE = 50     # Maximum fine after which the book is considered lost
    if days_overdue <= 0:
        return "The book is not overdue. No fines are charged."
    elif days_overdue <= GRACE_PERIOD:
        return "The book is within the grace period. No fines are charged."
    else:
        # Calculate the number of overdue days beyond the grace period
        overdue_days = days_overdue - GRACE_PERIOD
        # Calculate the fine
        fine = overdue_days * DAILY_FINE
        
        if fine > MAX_FINE:
            return "The fine has exceeded the MAXIMUM FINE. Please pay a fine of 50 rupees"
        else:
            return f"The total fine for the overdue book is: ₹{fine}"            
        
def add_new_book(mycursor, mydb):
    while True:
        try:
            while True:
                idd = int(input("Enter Book ID: "))
                mycursor.execute("SELECT * FROM Available_Books WHERE id = %s", (idd,))
                result = mycursor.fetchone()
                if idd < 0:
                    print("Book ID cannot be negative.")
                    continue
                if result:
                    print("Error: Book ID already exists in the table. Please try again.")
                else:
                    break
            
            name = input("Enter Book Name: ").strip()  # Strip whitespace from input
            if not name:  # Check if Book Name is empty
                print("Book Name cannot be left blank.")
                break
            
            subject = input("Enter Subject Name: ").strip()  # Strip whitespace from input
            if not subject:  # Check if Subject Name is empty
                print("Subject Name cannot be left blank.")
                break
            
            copies = int(input("Enter number of copies of the book: "))
            if copies < 0:
                print("Number of copies should be positive.")
                continue
            
            mycursor.execute(
                "INSERT INTO Available_Books (id, Name, Subject, Quantity) VALUES (%s, %s, %s, %s)",
                (idd, name, subject, copies)
            )
            mydb.commit()
            print("Data inserted successfully!!")
            
            if input("Do you wish to add more books? (y/n): ").lower() != 'y':
                break
        
        except ValueError:
            print("Invalid value for variable.")
            break
        except mysql.connector.Error as err:
            print(f"An error occurred: {err}")
            mydb.rollback()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

def remove_book(mycursor, mydb):
    try: 
        idd = int(input("Enter Book ID to remove the book: "))
        mycursor.execute("DELETE FROM Available_Books WHERE id = %s", (idd,))  # (idd,) is a tuple
        mydb.commit()  # because the execute method expects the parameters to be passed as a tuple or list
        if mycursor.rowcount > 0:  # mycursor.rowcount returns the number of rows affected by the last executed SQL statement.
            print("Book removed successfully.")  # If mycursor.rowcount > 0, it means that a row was successfully deleted 
        else:  # (i.e., a book with the specified ID existed and was removed).
            print("No Book with the entered ID exists.")
    except ValueError:
        print("Invalid value for variable.")
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        mydb.rollback()
    except:
        print("An unexpected error occurred.")

def update_quantity_of_books(mycursor, mydb):
    while True:
        try:
            # Prompt the user to choose between adding or removing book copies
            action = input("Would you like to Add or Remove copies of a book? (add/remove): ").strip().lower()
            if action not in ["add", "remove"]:
                print("Invalid choice. Please enter 'add' or 'remove'.")
                continue

            # Get the book ID from the user and ensure it is valid
            idd = int(input("Enter Book ID: "))
            if idd < 0:
                print("Book ID cannot be negative.")
                continue

            if action == "add":
                # For adding copies, prompt for the number of copies to add
                copies = int(input("Enter number of additional copies: "))
                if copies > 0:
                    # Update the database to increase the quantity of the specified book
                    mycursor.execute("UPDATE Available_Books SET Quantity = Quantity + %s WHERE id = %s", (copies, idd,))
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        print("Copies added successfully.")
                    else:
                        print("No book with the entered ID exists.")
                else:
                    print("Number of copies should be greater than 0.")

            elif action == "remove":
                # For removing copies, prompt for the number of copies to remove
                copies = int(input("Enter number of copies to remove: "))
                if copies > 0:
                    # Update the database to decrease the quantity of the specified book
                    mycursor.execute("UPDATE Available_Books SET Quantity = Quantity - %s WHERE id = %s AND Quantity >= %s", (copies, idd, copies))
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        print("Copies removed successfully.")
                    else:
                        print("No book with the entered ID exists or not enough copies available.")
                elif copies == 0:
                    print("No copies removed.")
                else:
                    print("Number of copies should be greater than 0.")

            # Ask the user if they want to perform another update
            if input("Do you wish to update more books? (y/n): ").strip().lower() != 'y':
                break

        except ValueError:
            # Handle cases where non-numeric values are entered
            print("Invalid input! Please enter numeric values for book ID and copies.")
        except mysql.connector.Error as err:
            # Handle database-related errors and rollback changes
            print(f"An error occurred: {err}")
            mydb.rollback()
        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unexpected error occurred: {e}")

def issue_book(mycursor, mydb):
    while True:
        try:
            idd = int(input("Enter Book ID: "))
            if idd < 0:
                print("Invalid value for variable!")
                continue
            
            S_Name = input("Enter Name of the student: ").strip()  # Strip whitespace from input
            if not S_Name:  # Check if S_Name is empty or just whitespace
                print("Student name cannot be blank or just white spaces.")
                break
            
            S_Class = int(input("Enter Class of the student(in integer value): "))
            if S_Class < 5 or S_Class > 12:
                print("Only students from grades 5 to 12 are allowed to borrow books.")
                break 
            else:
                # Check if the book exists
                mycursor.execute("SELECT * FROM Available_Books WHERE id = %s", (idd,))
                book = mycursor.fetchone()  # book, which will be a tuple containing the book's details (e.g., ID, Name, Subject, Quantity, etc.)
                
                if book:
                    # Check if the book has copies available
                    if book[3] > 0:  
                        # Check if the student has already borrowed this book
                        mycursor.execute("SELECT * FROM Books_issued WHERE id = %s AND S_Name = %s AND S_Class = %s", (idd, S_Name, S_Class))
                        existing_record = mycursor.fetchone()
                        
                        if existing_record:
                            print("This student has already borrowed this book.")
                        else:
                            issue_date = datetime.date.today()
                            status = 'Not overdue'  # initializes the status of the issued book to 'Not overdue'.
                            mycursor.execute(
                                "INSERT INTO Books_issued (id, Name, Subject, S_Name, S_Class, Issue_Date, Status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (idd, book[1], book[2], S_Name, S_Class, issue_date, status)
                            )
                            mycursor.execute(
                                "UPDATE Available_Books SET Quantity = Quantity - 1 WHERE id = %s", (idd,)
                            )
                            mydb.commit()
                            print("Book issued successfully.")
                    else:
                        print("No copies available.")
                else:
                    print("Book not found.")
                
                if input("Do you wish to issue more books? (y/n): ").lower() != 'y':
                    break
        except ValueError:
            print("Invalid value for variable.")
        except mysql.connector.Error as err:
            print(f"An error occurred: {err}")
            mydb.rollback()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def return_book(mycursor, mydb):
    while True:
        try:
            idd = int(input("Enter Book ID: "))
            S_Name = input("Enter Name of the student: ")
            S_Class = input("Enter Class of the student: ")

            # First, check if the book exists in Books_issued without considering S_Class
            mycursor.execute("SELECT * FROM Books_issued WHERE id = %s AND S_Name = %s", (idd, S_Name))
            issued_book = mycursor.fetchone()

            if issued_book:
                # Book found, now compare S_Class
                db_class = str(issued_book[4])  # Convert database class to string
                if db_class == S_Class:
                    issue_date = issued_book[5]
                    days_difference = (datetime.date.today() - issue_date).days
                    if days_difference > 15:
                        print(f"This book has been overdue by {days_difference - 15} days!")
                        days_overdue = days_difference - 15
                        result = calculate_fine(days_overdue)
                        print(result)
                    else:
                        print(f"This book is returned on time. It was borrowed for {days_difference} days.")
                    mycursor.execute("DELETE FROM Books_issued WHERE id = %s AND S_Name = %s AND S_Class = %s", (idd, S_Name, S_Class))
                    if mycursor.rowcount > 0:
                        mycursor.execute("UPDATE Available_Books SET Quantity = Quantity + 1 WHERE id = %s", (idd,))
                        mydb.commit()
                        print("Book returned successfully.")
                    else:
                        print("Failed to return book.")
                else:
                    print(f"Class mismatch. Book was issued to class {db_class}, but {S_Class} was entered.")
            else:
                print("No such book issued to this student.")

            if input("Do you wish to return more books? (y/n): ").lower() != 'y':
                break
        except ValueError:
            print("Invalid input. Please enter valid values.")
        except mysql.connector.Error as err:
            print(f"An error occurred: {err}")
            mydb.rollback()
        except:
            print("An error occurred. Please try again.")


def display_available_books(cursor):
    """Function to display available books in the library using tabulate."""
    print("The following books are available in the library:")
    
    # Query to fetch all available books
    q1 = "SELECT * FROM Available_Books"
    cursor.execute(q1)
    
    # Fetch all rows from the executed query
    books = cursor.fetchall()
    
    # Define the headers for the table
    headers = ["ID", "Name", "Subject", "Copies"]  # Adjust these as per your database schema

    # Use tabulate to format the table
    table = tabulate(books, headers=headers, tablefmt="fancy_outline")  # You can change the format if needed

    # Print the formatted table
    print(table)


def display_issued_books(mycursor, mydb):
    """Function to display issued books and update their status if overdue."""
    try:
        mycursor.execute("SELECT * FROM Books_issued")
        issued_books = mycursor.fetchall()  # issued_books is a list of tuples, where each tuple contains the details of a single issued book.
        
        if not issued_books:  # checks if the issued_books list is empty.
            print("No books have been issued.")
            return  # Exit the function if no books are issued

        today = datetime.date.today()  # retrieves the current date

        for book in issued_books:  # Each book is a tuple containing the details of one issued book
            issue_date = book[5]  # book[5] is the sixth element of the tuple, Issue_Date
            if issue_date is not None:
                delta = today - issue_date
                days_diff = delta.days
                if days_diff > 15:
                    mycursor.execute("UPDATE Books_issued SET Status='Overdue!' WHERE id=%s AND S_Name=%s AND S_Class=%s",
                                     (book[0], book[3], book[4]))
        
        mydb.commit()

        # Prepare to display issued books
        print("The following books have been issued to the respective students:")
        headers = ["ID", "Book Name", "Subject", "Student Name", "Student Class", "Issue Date", "Status"]
        
        # Use tabulate to format the table
        table = tabulate(issued_books, headers=headers, tablefmt="fancy_outline")  # You can change the format if needed

        # Print the formatted table
        print(table)

    except Exception as e:
        print("An error occurred. Please try again.")
        print(f"Error details: {e}")  # Optional: print the error details for debugging

def display_available_ebooks(mycursor):
    """Function to display available e-books in the library using tabulate."""
    try:
        print("The following e-books are available in the library:")
        mycursor.execute("SELECT * FROM Available_EBooks")  # Assuming the table for e-books is 'Available_EBooks'
        
        ebooks = mycursor.fetchall()
        
        if ebooks:  # Check if there are any e-books available
            headers = ["ID", "Name", "Subject"]  # Define the headers for the table
            
            # Use tabulate to format the table
            table = tabulate(ebooks, headers=headers, tablefmt="fancy_outline")  # You can change the format if needed
            
            # Print the formatted table
            print(table)
        else:
            print("No e-books available in the library.")
    
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
    except Exception as e:
        print("An error occurred. Please try again.")
        print(f"Error details: {e}")  # Optional: print the error details for debugging

def browse_ebooks(mycursor):
    """Function to print the Google Drive link for e-books."""
    try:
        g_drive_link = "https://drive.google.com/drive/folders/1Wryv9kTq5NfH_iscrSjEQSYaThTGFrJx?usp=drive_link"
        print(f"You can browse the E-Books in the following Google Drive folder: {g_drive_link}")
    except Exception as e:
        print(f"An error occurred while trying to display the Google Drive link: {e}")



# Function to fetch news from Currents API
def fetch_currents_api_news():#First choice(uses HTTPS to fetch news)
    api_url = "https://api.currentsapi.services/v1/latest-news"
    api_key = "eS59PGfR5TqisTXn08osnzpDgMChsNBRbtwlNFlWFvQyQpHJ"  # Your Currents API key

    try:
        response = requests.get(api_url, params={"apiKey": api_key})
        data = response.json() #json will convert the data from the website into python usable form.  
        #This is a dictionary containing the data from the API
        if data.get("news"): #Checks if the data dictionary has a value for the key 'news'
            return [{"title": item["title"], "url": item["url"]} for item in data["news"]] #this is list comprehension
        #A list of dictionaries
        #Without list comprehension:
            #result = []
            #for item in data["news"]:
                #result.append({"title": item["title"], "url": item["url"]})
            #return result
        else:
            print("Currents API returned no articles.")
    except Exception as e:
        print(f"Error fetching news from Currents API: {e}")
    return None

# Function to fetch news from RSS feeds
def fetch_rss_news():#Backup if currents api is not available
    rss_feeds = [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://rss.cnn.com/rss/edition.rss",
        "http://feeds.reuters.com/reuters/topNews"
    ]

    news = []
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)#A dictionary
            for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                news.append({"title": entry.title, "url": entry.link}) #Adds only the title and url because there are a lot of other parts(like author, website etc) 
        except Exception as e:
            print(f"Error parsing RSS feed {feed_url}: {e}")
    return news

# Unified function to fetch global news
def get_global_news():
    news = fetch_currents_api_news()
    if not news:  # Fallback to RSS feeds if Currents API fails or returns no articles
        print("No articles from Currents API. Using RSS feeds.")
        news = fetch_rss_news()
    return news 

# Function to display news to users
def display_news(): #MAIN FUNCTION THAT ACTUALLY PRINTS THE NEWS
    news = get_global_news()
    if news:
        print("Top Global News:") 
        for idx, article in enumerate(news, start=1): 
            print(f"{idx}. {article['title']} - {article['url']}") 
    else:
        print("No news articles available at the moment. Please try again later.")


def display_available_books_and_ebooks(mycursor):
    """Function to fetch and display available physical books and e-books in the library."""
    try:
        # Fetch and display physical books
        print("The following books are available in the library:")
        mycursor.execute("SELECT * FROM Available_Books")  # Assuming the table for physical books is 'Available_Books'
        
        books = mycursor.fetchall()
        
        if books:  # Check if there are any physical books available
            headers = ["ID", "Name", "Subject", "Copies"]  # Define headers for physical books
            book_table = tabulate(books, headers=headers, tablefmt="fancy_outline")  # Format the table
            
            # Print the formatted table
            print(book_table)
        else:
            print("No books available in the library.")
        
        print("\n")  # Blank line between the two sections
        
        # Fetch and display e-books
        print("The following E-Books are available in the library:")
        mycursor.execute("SELECT * FROM Available_EBooks")  # Assuming the table for e-books is 'Available_EBooks'
        
        ebooks = mycursor.fetchall()
        
        if ebooks:  # Check if there are any e-books available
            headers = ["ID", "Name", "Subject"]  # Define headers for e-books
            ebook_table = tabulate(ebooks, headers=headers, tablefmt="fancy_outline")  # Format the table
            
            # Print the formatted table
            print(ebook_table)
        else:
            print("No E-Books available in the library.")
    
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
    except Exception as e:
        print("An error occurred. Please try again.")
        print(f"Error details: {e}")  # Optional: print the error details for debugging

def check_password_strength(password):
    if len(password) < 6:
        return False

    if not re.search(r'[A-Z]', password) or \
       not re.search(r'[a-z]', password) or \
       not re.search(r'[0-9]', password) or \
       not re.search(r'[!@#$%^&*(),.?":{}|<>]', password): #slashes allow us to write the code in multiple lines in the same if condition
        return False

    if len(password)>15:
        return False

    return True

def generate_user_id(mycursor):
    while True:
        # Generate a random user ID: 1 alphabet + 2 digits
        alphabet = random.choice(string.ascii_letters)  # Choose one random alphabet
        digits = random.randint(100, 999)  # Generate a random number between 100 and 999
        user_id = f"{alphabet}{digits}"  # Combine them to form the user ID

        # Check if the user ID already exists in the database
        mycursor.execute("SELECT * FROM Users WHERE User_ID = %s", (user_id,))
        existing_user = mycursor.fetchone()

        if existing_user:
            print(f"User  ID '{user_id}' already exists. Generating a new one...")
        else:
            print(f"Generated User ID: {user_id}")
            return user_id


def add_new_user(mydb):
    try:
        mycursor = mydb.cursor()
        user_id = generate_user_id(mycursor)  # Generate a unique user ID
        
        # Display password requirements
        print("Password Requirements:")
        print("- At least 6 characters long")
        print("- Must contain at least one uppercase letter")
        print("- Must contain at least one lowercase letter")
        print("- Must contain at least one digit")
        print("- Must contain at least one special character (e.g., @, #, $, etc.)")
        
        password = maskpass.askpass("Enter Password: ")
        
        # Confirm the password
        confirm_password = maskpass.askpass("Confirm Password: ")

        if password != confirm_password:
            print("Passwords do not match. Please try again.")
            return

        if not check_password_strength(password):
            print("Password does not meet the requirements. Please try again.")
            return

        # Code to add the new user to the database
        mycursor.execute("INSERT INTO Users (User_ID, Password) VALUES (%s, %s)", (user_id, password))
        mydb.commit()
        print("New user added successfully.")
        print("Please remember this User ID and Password for future logins.")

    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        mydb.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")        

def update_user_password(mycursor, mydb):
    try:
        user_id = input("Enter User ID to update password: ")
        new_password = maskpass.askpass("Enter New Password: ")
        
        # Confirm the new password
        confirm_password = maskpass.askpass("Confirm New Password: ")

        if new_password != confirm_password:
            print("Passwords do not match. Please try again.")
            return

        if not check_password_strength(new_password):
            print("Password does not meet the requirements. Please try again.")
            return

        # Code to update the user's password in the database
        mycursor.execute("UPDATE Users SET Password = %s WHERE User_ID = %s", (new_password, user_id))
        mydb.commit()

        if mycursor.rowcount > 0:
            print("Password updated successfully.")
        else:
            print("No user found with the specified User ID.")

    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        mydb.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def display_all_users(mycursor, mydb):
    try:
        # Execute the query to fetch all users
        mycursor.execute("SELECT * FROM Users")
        users = mycursor.fetchall()  # Fetch all user records

        # Check if there are any users to display
        if users:
            # Prepare the headers and the data for tabulate
            headers = ["User  ID", "Password"]  
            print("\nList of Users:")
            print(tabulate(users, headers=headers, tablefmt='fancy_outline'))  # Using tabulate for neat display
        else:
            print("No users found in the database.")

    except mysql.connector.Error as err:
        print(f"An error occurred while fetching users: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def remove_user(mycursor, mydb):
    try:
        user_id = input("Enter User ID to remove: ") # Prompt for the User ID to remove

        # Check if the user exists before attempting to delete
        mycursor.execute("SELECT * FROM Users WHERE User_ID = %s", (user_id,))
        user = mycursor.fetchone()  # Fetch the user record

        if user:
            # Proceed to delete the user
            mycursor.execute("DELETE FROM Users WHERE User_ID = %s", (user_id,))
            mydb.commit()  # Commit the transaction

            if mycursor.rowcount > 0:  # Check if the deletion was successful
                print("User  removed successfully.")
            else:
                print("Failed to remove the user.")
        else:
            print("No user found with the specified User ID.")

    except ValueError:
        print("Invalid input. Please enter a valid User ID.")
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        mydb.rollback()  # Rollback in case of an error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main_menu():
    while True:        
        print("******************************************************************************************************************************************************************")
        print(' ')
        admin_login_banner = Text(""" █████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗    ███╗   ███╗███████╗███╗   ██╗██╗   ██╗
██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║    ████╗ ████║██╔════╝████╗  ██║██║   ██║
███████║██║  ██║██╔████╔██║██║██╔██╗ ██║    ██╔████╔██║█████╗  ██╔██╗ ██║██║   ██║
██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║    ██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║   ██║
██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║    ██║ ╚═╝ ██║███████╗██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                  """)

        console.print(admin_login_banner)
        print(' ')
        print("******************************************************************************************************************************************************************")
        print("\nMain Menu:")
        print("1) MANAGE BOOKS")
        print("2) MANAGE EBOOKS")
        print("3) MANAGE USERS")
        print("4) EXIT")
        
        choice = input("Please select an option (1-4): ")
        
        try:
            if choice == '1':
                manage_books_menu()
            elif choice == '2':
                manage_ebooks_menu()
            elif choice == '3':
                manage_users_menu()
            elif choice == '4':
                print("Exiting the program.")
                break
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"An error occurred in the main menu: {e}")

def manage_books_menu():
    while True:
        print("\nMANAGE BOOKS:")
        print("1) ADD NEW BOOK")
        print("2) REMOVE BOOK")
        print("3) UPDATE QUANTITY OF BOOKS")
        print("4) ISSUE BOOK")
        print("5) RETURN BOOK")
        print("6) DISPLAY AVAILABLE BOOKS")
        print("7) DISPLAY ISSUED BOOKS")
        print("8) BACK TO MAIN MENU")
        
        choice = input("Please select an option (1-8): ")
        
        try:
            if choice == '1':
                add_new_book(mycursor, mydb)
            elif choice == '2':
                remove_book(mycursor, mydb)
            elif choice == '3':
                update_quantity_of_books(mycursor, mydb)
            elif choice == '4':
                issue_book(mycursor, mydb)
            elif choice == '5':
                return_book(mycursor, mydb)
            elif choice == '6':
                display_available_books(mycursor)
            elif choice == '7':
                display_issued_books(mycursor, mydb)
            elif choice == '8':
                break
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"An error occurred while managing books: {e}")

def manage_ebooks_menu():
    while True:
        print("\nMANAGE EBOOKS:")
        print("1) DISPLAY AVAIALABLE EBOOKS")
        print("2) BACK TO MAIN MENU")
        
        choice = input("Please select an option (1-2): ")
        
        try:
            if choice == '1':
                display_available_ebooks(mycursor)
            elif choice == '2':
                break
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"An error occurred while managing ebooks: {e}")

def manage_users_menu():
    while True:
        print("\nMANAGE USERS:")
        print("1) ADD NEW USER")
        print("2) UPDATE USER PASSWORD")
        print("3) DISPLAY ALL USERS")
        print("4) REMOVE USER")
        print("5) BACK TO MAIN MENU")
        
        choice = input("Please select an option (1-4): ")
        
        try:
            if choice == '1':
                add_new_user(mydb)
            elif choice == '2':
                update_user_password(mycursor, mydb)
            elif choice == '3':
                display_all_users(mycursor, mydb)
            elif choice == '4':
                remove_user(mycursor, mydb)
            elif choice == '5':
                break
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"An error occurred while managing users: {e}")


while True:
    print("""
1. ADMIN LOGIN
2. DIGI-LIBRARY
3. EXIT
""")
    try:
        ch = int(input("Enter your choice: "))
        if ch == 1:
            Pass = maskpass.askpass("Enter Password: ")
            mycursor.execute("SELECT * FROM Admin_Login")
            user_data = mycursor.fetchone()#creates tuple userdata with 2 elements (username,pword)
            if user_data and Pass == user_data[1]:#and means 2 conditions. 1. if user_data(something was retrieved)
                print("You're logged in successfully")#2. Pass ==userdata[1] checks if given pword is same as actual password
             # Start the program
                try:
                    main_menu()
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")  
            else:
                print("Entered Password is wrong")
        elif ch==2:
            print("******************************************************************************************************************************************************************")
            print(' ')
            digi_library_banner = Text("""██████╗ ██╗ ██████╗ ██╗    ██╗     ██╗██████╗ ██████╗  █████╗ ██████╗ ██╗   ██╗
██╔══██╗██║██╔════╝ ██║    ██║     ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
██║  ██║██║██║  ███╗██║    ██║     ██║██████╔╝██████╔╝███████║██████╔╝ ╚████╔╝ 
██║  ██║██║██║   ██║██║    ██║     ██║██╔══██╗██╔══██╗██╔══██║██╔══██╗  ╚██╔╝  
██████╔╝██║╚██████╔╝██║    ███████╗██║██████╔╝██║  ██║██║  ██║██║  ██║   ██║   
╚═════╝ ╚═╝ ╚═════╝ ╚═╝    ╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
                                                                               """)
            console.print(digi_library_banner)
            print(' ')
            print("******************************************************************************************************************************************************************")

            try:
                validation=input("Are you an existing user?(y/n): ")
                if validation.lower()=='y':
            # Ask for user ID and password
                    user_id = input("Enter User ID: ")
                    password = maskpass.askpass("Enter Password: ")

                    # Retrieve the user data from the Users table based on the User_ID
                    query = "SELECT * FROM Users WHERE User_ID = %s"
                    mycursor.execute(query, (user_id,))
                    user_data = mycursor.fetchone()  # Fetch the result, returns a tuple (User_ID, Password)
                    if user_data and password == user_data[1]:
                        print("You're logged in successfully!")
                        while True:
                            print("""
            1) VIEW AVAILABLE E-BOOKS
            2) BROWSE E-BOOKS
            3) NEWS HEADLINES
            4) BROWSE WIKIPEDIA
            5) LOGOUT          
            """)
                            try:
                                ch = int(input("Enter your choice: "))
                                if ch == 1:
                                   display_available_ebooks(mycursor)
                                elif ch==2:
                                    browse_ebooks(mycursor)   
                                elif ch==3:
                                    try:
                                        display_news()
                                    except Exception as e:
                                        print(f"An error occurred: {e}")
                                elif ch == 4:  # Check if the user selected the option to browse news 
                                    try:
                                        wiki = wikipediaapi.Wikipedia( 
                                        language='en',
                                        extract_format=wikipediaapi.ExtractFormat.WIKI,
                                        user_agent='MyLibraryManager/1.0')  # English Wikipedia    
                                        # Get user input for the topic
                                        topic = input("Enter a topic to search on Wikipedia: ")
                                        page = wiki.page(topic)
                                        if page.exists():
                                            print(f"\nTitle: {page.title}")
                                            print(f"URL: {page.fullurl}\n")
                                            print("Summary:")
                                            print(page.summary[:500] + "...")  # Display the first 500 characters of the summary
                                        else:
                                            print("The topic you searched for does not exist on Wikipedia.")
                                    except ConnectionError:
                                        print("Could not connect to the browser!")
                                    except Exception as e:
                                        print(f"An error occurred while fetching data from Wikipedia:{e}")
                                elif ch==5:
                                    break
                                else:
                                    print("Invalid choice. Please choose a valid option.")
                            except ValueError:
                                print("Enter an appropriate value.")

                    else:
                        print("Invalid User ID or Password.")    
                elif validation.lower()=='n':
                    new_user=input("DO you want to create a new user account? (y/n): ")
                    if new_user.lower()=='y':
                        try:
                            add_new_user(mydb)
                        except ValueError:
                                print("Invalid input received.")

                        except mysql.connector.Error as err:
                                print(f"An error occurred: {err}")
                                mydb.rollback()  # Rollback in case of error         
                        except:
                                print("An error occurred. Please try again.") 
                    elif new_user.lower()=='n':
                        print("Exiting the program.")
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid choice.")
            except ValueError as err:
                print(f"An error occurred: {err}")
            except mysql.connector.Error as err:
                print(f"Error: {err}")  
            except:
                print("An error occurred. Please try again.")
        elif ch == 3:
            print("******************************************************************************************************************************************************************")
            print(' ')
            exit_banner = Text("""████████╗██╗  ██╗ █████╗ ███╗   ██╗██╗  ██╗    ██╗   ██╗ ██████╗ ██╗   ██╗██╗    ██████╗ ██╗   ██╗███████╗██╗██╗
╚══██╔══╝██║  ██║██╔══██╗████╗  ██║██║ ██╔╝    ╚██╗ ██╔╝██╔═══██╗██║   ██║██║    ██╔══██╗╚██╗ ██╔╝██╔════╝██║██║
   ██║   ███████║███████║██╔██╗ ██║█████╔╝      ╚████╔╝ ██║   ██║██║   ██║██║    ██████╔╝ ╚████╔╝ █████╗  ██║██║
   ██║   ██╔══██║██╔══██║██║╚██╗██║██╔═██╗       ╚██╔╝  ██║   ██║██║   ██║╚═╝    ██╔══██╗  ╚██╔╝  ██╔══╝  ╚═╝╚═╝
   ██║   ██║  ██║██║  ██║██║ ╚████║██║  ██╗       ██║   ╚██████╔╝╚██████╔╝██╗    ██████╔╝   ██║   ███████╗██╗██╗
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚═╝    ╚═════╝    ╚═╝   ╚══════╝╚═╝╚═╝
                                                                                                                """)
            
            console.print(exit_banner)
            print(' ')
            print("******************************************************************************************************************************************************************")
            break
        else:
            print("Invalid choice, please choose a valid option")
    except ValueError:
        print("Enter either 1,2 OR 3")
    except:
        print("An error occurred. Please try again.")
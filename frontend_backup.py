import mysql.connector
from pyswip import Prolog
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import threading

def create_db_connection():
    # Establishes a connection to the MySQL database and returns the connection object.
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='Air_Reserve_System'
        )
        print("MySQL Database connection successful")
    except Exception as e:
        print(f"The error '{e}' occurred")
        connection = None
    return connection

def display_main_menu():
    # Displays the main menu options to the user and returns the user's choice.
    recommended_airline = get_most_popular_airline()
    print("\nMain Menu:")
    print(f"Currently Popular Airline: {recommended_airline}")
    print("1. Add Reservation")
    print("2. Read Available Flights")
    print("3. Edit a Current Reservation")
    print("4. Delete a Reservation")
    print("5. Add a Flight")
    print("6. Remove a Flight")
    print("7. Exit")
    return input("Enter your choice (1-7): ")

def get_most_popular_airline():
    # Queries Prolog to find the most popular airline based on the number of bookings.
    prolog = Prolog()
    prolog.consult("backend.pl")
    result = list(prolog.query("most_popular_airline(Airline)"))
    return result[0]["Airline"] if result else "No recommendation available."

def add_flight(connection):
    print("Please enter the new flight details or press enter at any prompt to cancel.")
    
    airline_name = input("Airline Name: ")
    if not airline_name:
        print("Adding flight cancelled.")
        return

    flight_number = input("Flight Number: ")
    if not flight_number:
        print("Adding flight cancelled.")
        return

    departure_airport = input("Departure Airport: ")
    if not departure_airport:
        print("Adding flight cancelled.")
        return

    arrival_airport = input("Arrival Airport: ")
    if not arrival_airport:
        print("Adding flight cancelled.")
        return

    prolog = Prolog()
    prolog.consult("backend.pl")

    # Loop for departure datetime input validation
    while True:
        departure_datetime = input("Departure Date and Time (YYYY-MM-DD HH:MM:SS): ")
        if not departure_datetime:
            print("Adding flight cancelled.")
            return
        if list(prolog.query(f"valid_datetime_format('{departure_datetime}')")):
            break
        else:
            print("Invalid departure datetime format. Please enter the datetime in the format YYYY-MM-DD HH:MM:SS.")

    # Loop for arrival datetime input validation
    while True:
        arrival_datetime = input("Arrival Date and Time (YYYY-MM-DD HH:MM:SS): ")
        if not arrival_datetime:
            print("Adding flight cancelled.")
            return
        if list(prolog.query(f"valid_datetime_format('{arrival_datetime}')")):
            break
        else:
            print("Invalid arrival datetime format. Please enter the datetime in the format YYYY-MM-DD HH:MM:SS.")
    
    # Checks if the departure is before the arrival
    time_check = list(prolog.query(f"is_departure_before_arrival('{departure_datetime}', '{arrival_datetime}', Result)."))
    if not time_check or time_check[0]["Result"] == 'false':
        print("Error: Arrival Time is before Departure Time.")
        return

    max_capacity = input("Maximum Capacity: ")
    if not max_capacity:
        print("Adding flight cancelled.")
        return
    try:
        max_capacity = int(max_capacity)
        if max_capacity <= 0:
            print("Maximum capacity must be a positive integer.")
            return
    except ValueError:
        print("Invalid input for maximum capacity.")
        return

    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO Flights (
            airline_name, flight_number, departure_airport, arrival_airport, 
            departure_datetime, arrival_datetime, max_capacity
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (airline_name, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime, max_capacity))
        connection.commit()
        print("Flight added successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


def remove_flight(connection):
    run_list_flights_in_thread(connection)
    flight_id = input("Enter the Flight ID you wish to remove (or input 0 to exit): ")
    
    if flight_id == '0':
        print("Exiting flight removal process.")
        return

    prolog = Prolog()
    prolog.consult("backend.pl")

    # Verify if the user wants to proceed with deletion
    confirm = input(f"Are you sure you want to remove Flight ID {flight_id}? (yes/no): ").lower()
    if confirm == 'yes':
        result = list(prolog.query(f"delete_flight({flight_id}, Success)."))
        if result and result[0]['Success'] == 'true':
            print("Flight removed successfully.")
        else:
            print("An error occurred while trying to remove the flight.")
    else:
        print("Flight removal cancelled.")


def add_passenger(connection, passenger_details):
    first_name, last_name, email, phone_number = passenger_details
    try:
        cursor = connection.cursor()
        query = "INSERT INTO Passengers (first_name, last_name, email, phone_number) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, (first_name, last_name, email, phone_number))
        connection.commit()
        passenger_id = cursor.lastrowid
        print(f"Passenger added successfully. Passenger ID: {passenger_id}")
        return passenger_id
    except mysql.connector.Error as e:
        print(f"Failed to add passenger. MySQL Error: {e}")
        return None


def edit_reservation(connection):
    list_current_reservations(connection)
    reservation_id = input("Enter the Reservation ID you wish to edit (or input 0 to exit): ")

    if reservation_id == '0':
        print("Exiting edit reservation process.")
        return

    prolog = Prolog()
    prolog.consult("backend.pl")
    
    # Check if the reservation ID exists
    exists_result = list(prolog.query(f"reservation_exists({reservation_id}, Exists)"))
    if not exists_result or exists_result[0]["Exists"] == "false":
        print("No reservation ID found.")
        return

    run_list_flights_in_thread(connection)
    new_flight_id = input("Enter new Flight ID: ")
    new_seat_number = input("Enter new Seat Number (e.g., 12A): ")

    # Check if the new flight ID is valid
    if not validate_flight_id(new_flight_id):
        print("Invalid Flight ID. Please try again.")
        return
    
    # Check if the seat is already taken
    if not validate_seat_number(new_flight_id, new_seat_number):
        print("This seat is already taken. Please choose a different seat.")
        return
    
    # Check if the new flight has capacity
    can_book_result = list(prolog.query(f"can_book_flight({new_flight_id}, CanBook)"))
    if not can_book_result or can_book_result[0]["CanBook"] == "false":
        print("Cannot change to the selected flight due to max capacity.")
        return

    # Perform the update in the database
    result = list(prolog.query(f"edit_reservation({reservation_id}, {new_flight_id}, '{new_seat_number}', Success)."))
    if result and result[0]['Success'] == 'true':
        print("Reservation updated successfully.")
    else:
        print("Failed to update the reservation.")


def delete_reservation(connection):
    list_current_reservations(connection)
    reservation_id = input("Enter the Reservation ID you wish to delete (or input 0 to exit): ")
    
    if reservation_id == '0':
        print("Exiting delete reservation process.")
        return
    
    prolog = Prolog()
    prolog.consult("backend.pl")
    result = list(prolog.query(f"delete_reservation({reservation_id}, Success)"))
    
    if result and result[0]["Success"] == "true":
        print("Reservation deleted successfully.")
        connection.commit()
    else:
        print("Reservation ID not found. No deletion performed.")

def list_flights(connection):
    window = tk.Tk()
    window.title("Available Flights")
    window.geometry("1140x500")  # Adjust the size as needed

    # Define the columns
    columns = ("flight_id", "airline_name", "flight_number", "departure", "arrival", "departure_time", "arrival_time")

    tree = ttk.Treeview(window, columns=columns, show="headings")
    tree.heading("flight_id", text="Flight ID")
    tree.heading("airline_name", text="Airline")
    tree.heading("flight_number", text="Flight Number")
    tree.heading("departure", text="Departure")
    tree.heading("arrival", text="Arrival")
    tree.heading("departure_time", text="Departure Time")
    tree.heading("arrival_time", text="Arrival Time")

    tree.column("flight_id", width=80)
    tree.column("airline_name", width=150)
    tree.column("flight_number", width=100)
    tree.column("departure", width=250)
    tree.column("arrival", width=250)
    tree.column("departure_time", width=150)
    tree.column("arrival_time", width=150)

    # scrollbar adding
    scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")

    tree.pack(side=tk.LEFT, fill="both", expand=True)

    # Retrieving flight data from database
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT flight_id, airline_name, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime FROM Flights ORDER BY departure_datetime;")
    flights = cursor.fetchall()

    for flight in flights:
        tree.insert("", tk.END, values=(flight["flight_id"], flight["airline_name"], flight["flight_number"],
                                         flight["departure_airport"], flight["arrival_airport"], 
                                         flight["departure_datetime"], flight["arrival_datetime"]))

    window.mainloop()

def run_list_flights_in_thread(connection):
    flight_thread = threading.Thread(target=list_flights, args=(connection,))
    flight_thread.start()

def validate_flight_id(flight_id):
    prolog = Prolog()
    prolog.consult("backend.pl")  
    query = f"flight_id_exists({flight_id}, Exists)."
    result = list(prolog.query(query))
    if result and result[0]['Exists'] == 'true':
        return True
    else:
        return False

def validate_seat_number(flight_id, seat_number):
    prolog = Prolog()
    prolog.consult("backend.pl") 
    query = f"seat_number_available({flight_id}, '{seat_number}', Available)."
    result = list(prolog.query(query))
    if result and result[0]['Available'] == 'true':
        return True
    else:
        return False

def get_valid_datetime(prompt):
    prolog = Prolog()
    prolog.consult("backend.pl")
    while True:
        datetime_input = input(prompt)
        if list(prolog.query(f"valid_datetime_format('{datetime_input}')")):
            return datetime_input
        else:
            print("Invalid datetime format. Please enter the datetime in the format YYYY-MM-DD HH:MM:SS.")

def list_current_reservations(connection): # Did not use Prolog due to ODBC complications
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT r.reservation_id, p.first_name, p.last_name, r.flight_id, r.seat_number, r.booking_status
    FROM Reservations r
    JOIN Passengers p ON r.passenger_id = p.passenger_id
    ORDER BY r.reservation_id;
    """
    cursor.execute(query)
    reservations = cursor.fetchall()

    if reservations:
        print("Current Reservations:")
        for reservation in reservations:
            print(f"Reservation ID: {reservation['reservation_id']}, Passenger: {reservation['first_name']} {reservation['last_name']}, Flight ID: {reservation['flight_id']}, Seat: {reservation['seat_number']}, Status: {reservation['booking_status']}")
    else:
        print("No current reservations found.")

def can_book_flight_via_prolog(flight_id):
    prolog = Prolog()
    prolog.consult("backend.pl")
    query = f"can_book_flight({flight_id}, CanBook)."
    result = list(prolog.query(query))
    if result and result[0]["CanBook"] == "true":
        return True
    else:
        return False

def make_reservation(connection, passenger_id, flight_id, seat_number):
    prolog = Prolog()
    prolog.consult("backend.pl")
    can_book = list(prolog.query(f"can_book_flight({flight_id}, CanBook)"))
    if can_book and can_book[0]["CanBook"] == "true":
        try:
            cursor = connection.cursor()
            query = "INSERT INTO Reservations (passenger_id, flight_id, seat_number, booking_status) VALUES (%s, %s, %s, 'confirmed');"
            cursor.execute(query, (passenger_id, flight_id, seat_number))
            connection.commit()
            print("Reservation made successfully!")
        except mysql.connector.Error as e:
            print(f"Failed to make reservation. MySQL Error: {e}")
    else:
        print("Cannot make reservation: Flight is fully booked.")

def get_user_input_for_passenger():
    print("Please enter your personal details or press enter at any prompt to cancel.")

    first_name = input("First Name: ")
    if not first_name.strip():
        print("Adding passenger cancelled.")
        return None, None, None, None  # Returning a tuple of None values

    last_name = input("Last Name: ")
    if not last_name.strip():
        print("Adding passenger cancelled.")
        return None, None, None, None

    email = input("Email: ")
    if not email.strip():
        print("Adding passenger cancelled.")
        return None, None, None, None

    phone_number = input("Phone Number: ")
    if not phone_number.strip():
        print("Adding passenger cancelled.")
        return None, None, None, None

    return first_name, last_name, email, phone_number



def choose_flight_and_seat(connection):
    run_list_flights_in_thread(connection)
    flight_id = input("Please enter the flight ID you wish to book: ")
    while not validate_flight_id(flight_id):
        print("Invalid flight ID. Please choose a valid flight ID from the list.")
        flight_id = input("Please enter the flight ID you wish to book: ")
    seat_number = input("Please enter your preferred seat number (e.g., 12A): ")
    while not validate_seat_number(flight_id, seat_number):
        print("This seat is already taken. Please choose a different seat.")
        seat_number = input("Please enter your preferred seat number (e.g., 12A): ")
    return flight_id, seat_number

def main():
    connection = create_db_connection()
    if connection:
        print("Welcome to the Airline Reservation System!")
        while True:
            user_choice = display_main_menu()
            if user_choice == '1':
                passenger_details = get_user_input_for_passenger()
                if None in passenger_details:
                    continue  # Skip adding the passenger if the operation was cancelled
                passenger_id = add_passenger(connection, passenger_details)
                if passenger_id is not None:
                    flight_id, seat_number = choose_flight_and_seat(connection)
                    make_reservation(connection, passenger_id, flight_id, seat_number)
                else:
                    print("Failed to add passenger.")
            elif user_choice == '2':
                run_list_flights_in_thread(connection)
            elif user_choice == '3':
                edit_reservation(connection)
            elif user_choice == '4':
                delete_reservation(connection)
            elif user_choice == '5':
                add_flight(connection)
            elif user_choice == '6':
                remove_flight(connection)
            elif user_choice == '7':
                print("Exiting the Airline Reservation System.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    main()
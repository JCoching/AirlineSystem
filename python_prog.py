import mysql.connector

def create_db_connection():
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
    print("\nMain Menu:")
    print("1. Add Reservation")
    print("2. Read Available Flights")
    print("3. Edit a Current Reservation")
    print("4. Delete a Reservation")
    print("5. Add a Flight")  # New option for adding a flight
    print("6. Remove a Flight")  # New option for removing a flight
    print("7. Exit")
    choice = input("Enter your choice (1-7): ")
    return choice

def add_flight(connection):
    try:
        print("Please enter the new flight details.")
        airline_name = input("Airline Name: ")
        flight_number = input("Flight Number: ")
        departure_airport = input("Departure Airport: ")
        arrival_airport = input("Arrival Airport: ")
        departure_datetime = input("Departure Date and Time (YYYY-MM-DD HH:MM:SS): ")
        arrival_datetime = input("Arrival Date and Time (YYYY-MM-DD HH:MM:SS): ")
        max_capacity = input("Maximum Capacity: ")

        # Validate inputs (simple validation for demonstration)
        if not all([airline_name, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime, max_capacity]):
            print("All fields are required.")
            return

        # Convert max_capacity to integer and validate
        max_capacity = int(max_capacity)
        if max_capacity <= 0:
            print("Maximum capacity must be a positive integer.")
            return

        cursor = connection.cursor()
        query = "INSERT INTO Flights (airline_name, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime, max_capacity) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(query, (airline_name, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime, max_capacity))
        connection.commit()
        print("Flight added successfully.")
    except mysql.connector.Error as e:
        print(f"Failed to add flight. MySQL Error: {e}")
    except ValueError:
        print("Invalid input. Maximum Capacity must be an integer.")
    except Exception as e:
        print(f"An error occurred: {e}")

def remove_flight(connection):
    list_flights(connection)  # Show the list of flights
    flight_id = input("Enter the Flight ID you wish to remove (or input 0 to exit): ")
    
    if flight_id == '0':
        print("Exiting flight removal process.")
        return
    
    cursor = connection.cursor()
    # Check if the flight exists
    cursor.execute("SELECT * FROM Flights WHERE flight_id = %s;", (flight_id,))
    if cursor.fetchone():
        # Confirm before deleting
        confirm = input(f"Are you sure you want to remove Flight ID {flight_id}? (yes/no): ").lower()
        if confirm == 'yes':
            delete_query = "DELETE FROM Flights WHERE flight_id = %s;"
            cursor.execute(delete_query, (flight_id,))
            connection.commit()
            print("Flight removed successfully.")
        else:
            print("Flight removal cancelled.")
    else:
        print("Flight not found.")

def add_passenger(connection, passenger_details):
    cursor = connection.cursor(dictionary=True)
    email = passenger_details[2]
    cursor.execute("SELECT passenger_id FROM Passengers WHERE email = %s;", (email,))
    existing_passenger = cursor.fetchone()
    if existing_passenger:
        print(f"Passenger with email {email} already exists. Passenger ID: {existing_passenger['passenger_id']}")
        return existing_passenger['passenger_id']
    else:
        query = "INSERT INTO Passengers (first_name, last_name, email, phone_number) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, passenger_details)
        connection.commit()
        print("Passenger added successfully. Passenger ID:", cursor.lastrowid)
        return cursor.lastrowid

def edit_reservation(connection):
    list_current_reservations(connection)
    reservation_id = input("Enter the Reservation ID you wish to edit (input 0 to exit): ")

    if reservation_id =='0':
        print("Exiting edit reservation process.")
        return
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Reservations WHERE reservation_id = %s;", (reservation_id,))
    reservation = cursor.fetchone()

    if reservation:
        print(f"Editing reservation ID: {reservation_id}")
        new_flight_id = input("Enter new Flight ID (leave blank to keep current): ")
        new_seat_number = input("Enter new Seat Number (leave blank to keep current): ")
        print("Reservation updated successfully.")
    else:
        print("Reservation not found.")

def delete_reservation(connection):
    list_current_reservations(connection)  # Show the list of current reservations
    reservation_id = input("Enter the Reservation ID you wish to delete (or input 0 to exit): ")
    
    # Option to exit
    if reservation_id == '0':
        print("Exiting delete reservation process.")
        return

    cursor = connection.cursor()
    # Check if the reservation exists
    cursor.execute("SELECT * FROM Reservations WHERE reservation_id = %s;", (reservation_id,))
    if cursor.fetchone():
        # Confirm before deleting
        confirm = input(f"Are you sure you want to delete reservation ID {reservation_id}? (yes/no): ").lower()
        if confirm == 'yes':
            delete_query = "DELETE FROM Reservations WHERE reservation_id = %s;"
            cursor.execute(delete_query, (reservation_id,))
            connection.commit()
            print("Reservation deleted successfully.")
        else:
            print("Deletion cancelled.")
    else:
        print("Reservation not found.")

def list_flights(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT flight_id, airline_name, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime FROM Flights ORDER BY departure_datetime;")
    flights = cursor.fetchall()
    if flights:
        print("Available Flights:")
        for flight in flights:
            print(f"Flight ID: {flight['flight_id']}, Airline: {flight['airline_name']}, Flight Number: {flight['flight_number']}, Departure: {flight['departure_airport']} -> Arrival: {flight['arrival_airport']}, Departure Time: {flight['departure_datetime']}, Arrival Time: {flight['arrival_datetime']}")
    else:
        print("No available flights.")

def validate_flight_id(connection, flight_id):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Flights WHERE flight_id = %s;", (flight_id,))
    return cursor.fetchone()[0] == 1

def validate_seat_number(connection, flight_id, seat_number):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Reservations WHERE flight_id = %s AND seat_number = %s;", (flight_id, seat_number))
    return cursor.fetchone()[0] == 0

def list_current_reservations(connection):
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


def make_reservation(connection, reservation_details):
    flight_id = reservation_details[1]  # Assuming reservation_details[1] is the flight_id

    # Check if the flight has available capacity
    if check_flight_capacity(connection, flight_id):
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Reservations (passenger_id, flight_id, seat_number, booking_status) VALUES (%s, %s, %s, %s);", reservation_details)
        connection.commit()
        print("Reservation made successfully")
    else:
        print("Cannot make reservation: Flight is fully booked.")


def get_user_input_for_passenger():
    print("Please enter your personal details.")
    return input("First Name: "), input("Last Name: "), input("Email: "), input("Phone Number: ")

def choose_flight_and_seat(connection):
    list_flights(connection)
    flight_id = input("Please enter the flight ID you wish to book: ")
    while not validate_flight_id(connection, flight_id):
        print("Invalid flight ID. Please choose a valid flight ID from the list above.")
        flight_id = input("Please enter the flight ID you wish to book: ")
    seat_number = input("Please enter your preferred seat number (e.g., 12A): ")
    while not validate_seat_number(connection, flight_id, seat_number):
        print("This seat is already taken. Please choose a different seat.")
        seat_number = input("Please enter your preferred seat number (e.g., 12A): ")
    return flight_id, seat_number

def check_flight_capacity(connection, flight_id):
    cursor = connection.cursor()
    # Query to count the number of reservations for the given flight_id
    cursor.execute("SELECT COUNT(*) FROM reservations WHERE flight_id = %s;", (flight_id,))
    reservations_count = cursor.fetchone()[0]

    # Query to get the max capacity of the flight
    cursor.execute("SELECT max_capacity FROM flights WHERE flight_id = %s;", (flight_id,))
    max_capacity = cursor.fetchone()[0]

    # Check if the flight has available seats
    if reservations_count < max_capacity:
        return True  # Flight has available seats
    else:
        return False  # Flight is fully booked


def main():
    connection = create_db_connection()
    if connection:
        print("Welcome to the Airline Reservation System!")
        while True:
            user_choice = display_main_menu()
            if user_choice == '1':
                first_name, last_name, email, phone_number = get_user_input_for_passenger()
                passenger_id = add_passenger(connection, (first_name, last_name, email, phone_number))
                flight_id, seat_number = choose_flight_and_seat(connection)
                make_reservation(connection, (passenger_id, flight_id, seat_number, 'confirmed'))
                print("Your reservation has been made successfully!")
            elif user_choice == '2':
                list_flights(connection)
            elif user_choice == '3':
                edit_reservation(connection)
                # Implement function to edit reservation
            elif user_choice == '4':
                delete_reservation(connection)
            elif user_choice == '5':
                add_flight(connection)  # Handle adding a flight
            elif user_choice == '6':
                remove_flight(connection)  # Handle removing a flight
            elif user_choice == '7':
                print("Exiting the Airline Reservation System.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    main()

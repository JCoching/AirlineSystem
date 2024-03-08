% Use the ODBC library for database connectivity.
:- use_module(library(odbc)).

% Establishes a connection to the database.
connect_to_database(Connection) :-
    odbc_connect('AirSystem', Connection, [user('root'), password(''), open(once)]).

% Determines the most popular airline based on reservation counts.
most_popular_airline(Airline) :-
    connect_to_database(Connection),
    odbc_prepare(Connection,
                 'SELECT airline_name, COUNT(*) AS count FROM flights JOIN reservations ON flights.flight_id = reservations.flight_id GROUP BY airline_name ORDER BY count DESC LIMIT 1',
                 [], Statement),
    odbc_execute(Statement, [], row(Airline, _)),
    odbc_free_statement(Statement),
    odbc_disconnect(Connection).

% -- ADD --

% Makes a reservation if the flight has capacity.
make_reservation(PassengerID, FlightID, SeatNumber, Success) :-
    can_book_flight(FlightID, CanBook),
    (
        CanBook = true ->
        (
            connect_to_database(Connection),
            odbc_prepare(Connection, 
                         'INSERT INTO Reservations (passenger_id, flight_id, seat_number, booking_status) VALUES (?, ?, ?, "confirmed")', 
                         [integer, integer, varchar], 
                         InsertStatement),
            odbc_execute(InsertStatement, [PassengerID, FlightID, SeatNumber]),
            odbc_free_statement(InsertStatement),
            odbc_disconnect(Connection),
            Success = true
        )
        ;
        Success = false
    ).

% -- UPDATE --

% Edits an existing reservation in the database.
edit_reservation(ReservationID, NewFlightID, NewSeatNumber, Success) :-
    connect_to_database(Connection),
    odbc_prepare(Connection,
                 'UPDATE Reservations SET flight_id = ?, seat_number = ? WHERE reservation_id = ?',
                 [integer, varchar, integer],
                 Statement),
    odbc_execute(Statement, [NewFlightID, NewSeatNumber, ReservationID]),
    odbc_free_statement(Statement),
    odbc_disconnect(Connection),
    Success = true.

% -- DELETE --

% Deletes a reservation given its ID, if it exists.
delete_reservation(ReservationID, Success) :-
    reservation_exists(ReservationID, Exists),
    (
        Exists = true ->
        (
            connect_to_database(Connection),
            odbc_prepare(Connection, 'DELETE FROM reservations WHERE reservation_id = ?', [integer], DeleteStatement),
            odbc_execute(DeleteStatement, [ReservationID], _),
            odbc_free_statement(DeleteStatement),
            odbc_disconnect(Connection),
            Success = true
        )
        ;
        Success = false
    ).

% Deletes a flight given its ID.
delete_flight(FlightID, Success) :-
    connect_to_database(Connection),
    odbc_prepare(Connection, 'DELETE FROM Flights WHERE flight_id = ?', [integer], Statement),
    odbc_execute(Statement, [FlightID], _),
    odbc_free_statement(Statement),
    odbc_disconnect(Connection),
    Success = true.

% -- VALIDATIONS --

% Checks if a flight ID exists in the system.
flight_id_exists(FlightID, Exists) :-
    connect_to_database(Connection),
    odbc_prepare(Connection, 'SELECT COUNT(*) FROM Flights WHERE flight_id = ?', [integer], Statement),
    odbc_execute(Statement, [FlightID], row(Count)),
    odbc_free_statement(Statement),
    odbc_disconnect(Connection),
    (Count > 0 -> Exists = true; Exists = false).

% Checks if a seat number for a given flight is available.
seat_number_available(FlightID, SeatNumber, Available) :-
    connect_to_database(Connection),
    odbc_prepare(Connection, 'SELECT COUNT(*) FROM Reservations WHERE flight_id = ? AND seat_number = ?', [integer, varchar], Statement),
    odbc_execute(Statement, [FlightID, SeatNumber], row(Count)),
    odbc_free_statement(Statement),
    odbc_disconnect(Connection),
    (Count = 0 -> Available = true; Available = false).

% Determines if booking is allowed for a given flight based on its capacity.
can_book_flight(FlightID, CanBook) :-
    connect_to_database(Connection),
    % Query to get the current number of reservations for the flight.
    odbc_prepare(Connection, 'SELECT COUNT(*) FROM reservations WHERE flight_id = ?', [integer], CountStatement),
    odbc_execute(CountStatement, [FlightID], row(ReservationCount)),
    % Query to get the maximum capacity of the flight.
    odbc_prepare(Connection, 'SELECT max_capacity FROM flights WHERE flight_id = ?', [integer], CapacityStatement),
    odbc_execute(CapacityStatement, [FlightID], row(MaxCapacity)),
    odbc_free_statement(CountStatement),
    odbc_free_statement(CapacityStatement),
    odbc_disconnect(Connection),
    % Determine booking availability.
    (ReservationCount < MaxCapacity -> CanBook = true ; CanBook = false).

% Checks if a given reservation ID exists in the system.
reservation_exists(ReservationID, Exists) :-
    connect_to_database(Connection),
    odbc_prepare(Connection, 'SELECT COUNT(*) FROM reservations WHERE reservation_id = ?', [integer], Statement),
    odbc_execute(Statement, [ReservationID], row(Count)),
    odbc_free_statement(Statement),
    odbc_disconnect(Connection),
    (Count > 0 -> Exists = true; Exists = false).


% Checks if a given datetime string matches the YYYY-MM-DD HH:MM:SS format
valid_datetime_format(DateTime) :-
    string_codes(DateTime, Codes),
    length(Codes, 19),
    nth0(4, Codes, 45), % '-'
    nth0(7, Codes, 45), % '-'
    nth0(10, Codes, 32), % ' '
    nth0(13, Codes, 58), % ':'
    nth0(16, Codes, 58), % ':'
    all_codes_digits_except(Codes, [4, 7, 10, 13, 16]).

%checks if all codes are digits except for specified positions
all_codes_digits_except([], _).
all_codes_digits_except([Code|Codes], Exceptions) :-
    (   memberchk(Code, [45, 32, 58]) % '-', ' ', ':'
    ->  true
    ;   Code >= 48, Code =< 57  % '0'-'9'
    ),
    all_codes_digits_except(Codes, Exceptions).

%checks if the departure datetime is before the arrival datetime.
is_departure_before_arrival(Departure, Arrival, Result) :-
    ( Departure @< Arrival -> Result = true ; Result = false ).

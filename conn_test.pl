% Load the ODBC library
:- use_module(library(odbc)).

% Connect to the database
connect_to_database(Connection) :-
    odbc_connect('AirSystem', Connection, 
                 [user('root'), 
                  password(''), 
                  open(once)]).

% Perform test query
test_query(Connection) :-
    odbc_query(Connection, 'SELECT * FROM passengers LIMIT 5', Row),
    format('Row: ~w~n', [Row]),
    fail. 

test_query(_).

% Main predicate to run the test
run_test :-
    connect_to_database(Connection),
    test_query(Connection),
    odbc_disconnect(Connection),
    write('Test completed successfully.').



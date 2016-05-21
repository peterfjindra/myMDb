"""
db_personal.py
language: python2
author: Peter Jindra, peterfjindra@gmail.com

A series of functions used for myMDb project.
These functions focus specifically on updating and querying the local PostgreSQL database.
"""
import psycopg2
from temp_objects import *

cur = None

"""
Adds a person to ACTORS, DIRECTORS, or WRITERS
Note that an Actor, Director, and Writer are treated as separate persons, e.g.
Clint Eastwood might exist in the ACTORS and DIRECTORS tables,
and as far as the database knows, they are 2 separate entities.
@params:
	new_person: tempPerson object, the person to add to the db
@return:
	True if the person is added
	False if the person already existed
"""
def addPerson(new_person):
	if hasPerson(new_person, "", False):
		return False
	if new_person.p_type == "actor":
		table = "ACTORS"
	elif new_person.p_type == "director":
		table = "DIRECTORS"
	else:
		table = "WRITERS"
	cur.execute("INSERT INTO " + table + "(NAME) VALUES  ('" + new_person.name + "')")
	return True

"""
Adds a movie to MOVIES
Only title, year, runtime, mpaa, and rating are stored in the MOVIES table
Movies are connected to people with the ACTING, DIRECTING, and WRITING tables
@params:
	new_movie: tempMovie object, the movie to add to the db
	passw:     string, the password to access the db carried over so the user doesn't have to enter it again
@return:
	True if the movie was added
	False if the movie already existed
"""
def addMovie(new_movie, passw):
	conn = psycopg2.connect(database="test", user="postgres", password=passw, host="127.0.0.1", port="5432")
	global cur
	cur = conn.cursor()
	if hasMovie(new_movie):
		return False
	values = "('" + new_movie.title + "','" + new_movie.year + "','" + new_movie.runtime + "','" + new_movie.mpaa + \
		    "','" + new_movie.rating + "'," + str(new_movie.watched) + "," + str(new_movie.own) + ")"
	#print "INSERT INTO MOVIES (TITLE,YEAR,RUNTIME,MPAA,RATING) VALUES " + values
	cur.execute("INSERT INTO MOVIES (TITLE,YEAR,RUNTIME,MPAA,RATING,WATCHED,OWN) VALUES " + values)
	for director in new_movie.director:
		new_director = tempPerson(director.upper(), 'director')
		addPerson(new_director)
		addRole(new_movie, new_director)
	for writer in new_movie.writer:
		new_writer = tempPerson(writer.upper(), 'writer')
		addPerson(new_writer)
		addRole(new_movie, new_writer)
	for actor in new_movie.cast:
		new_actor = tempPerson(actor.upper(), 'actor')
		addPerson(new_actor)
		addRole(new_movie, new_actor)
	conn.commit()
	conn.close()
	return True

"""
Adds foreign keys for a person and movie to ACTING, DIRECTING, or WRITING
@params:
	amovie:  tempMovie object
	aperson: tempPerson object
@return:
	False if one of the two objects does not exist, entry is unsuccessful
	True if the entry is successful
"""
def addRole(amovie, aperson):
	if not hasMovie(amovie) or not hasPerson(aperson, "", False):
		return False
	else:
		if aperson.p_type == "actor":
			table = "ACTING"
			id_type = "A_ID"
		elif aperson.p_type == "director":
			table = "DIRECTING"
			id_type = "D_ID"
		else:
			table = "WRITING"
			id_type = "W_ID"
		movie_id = getMovieID(amovie)
		person_id = getPersonID(aperson)
		cur.execute("INSERT INTO " + table + "(M_ID, " + id_type + ") VALUES  (" + str(movie_id) + ", " + str(person_id) + ")")
		return True

#def manualAddMovie():
"""
Searches for movies with a matching title.
@params:
	title: string, the title of the movie being searched for
	passw: string, the password to access the db carried over so the user doesn't have to enter it again
@returns:
	an array of tempMovie objects that match the title
	None if no movies are found
"""
def getMovies(title, passw):
	conn = psycopg2.connect(database="test", user="postgres", password=passw, host="127.0.0.1", port="5432")
	global cur
	cur = conn.cursor()
	cur.execute("SELECT * from MOVIES WHERE title = " + "'" + title + "'")
	result = cur.fetchall()
	if result != []:
		found_movies = []
		for row in result:
			cur.execute("SELECT ACTORS.name FROM MOVIES, ACTORS, ACTING WHERE MOVIES.id = " + str(row[0]) + " AND MOVIES.id = ACTING.m_id AND ACTORS.id = ACTING.a_id")
			actors = []
			for entry in cur.fetchall():
				actors.append(entry[0])
			cur.execute("SELECT DIRECTORS.name FROM MOVIES, DIRECTORS, DIRECTING WHERE MOVIES.id = " + str(row[0]) + " AND MOVIES.id = DIRECTING.m_id AND DIRECTORS.id = DIRECTING.d_id")
			directors = []
			for entry in cur.fetchall():
				directors.append(entry[0])
			cur.execute("SELECT WRITERS.name FROM MOVIES, WRITERS, WRITING WHERE MOVIES.id = " + str(row[0]) + " AND MOVIES.id = WRITING.m_id AND WRITERS.id = WRITING.w_id")
			writers = []
			for entry in cur.fetchall():
				writers.append(entry[0])			
			movie = tempMovie(row[1], directors, writers, actors, row[2], row[3], row[4], row[5], row[6], row[7])
			found_movies.append(movie)
		conn.close()
		return found_movies

"""
Given a person, returns info from the Movies table for all the films they've worked on.
@params:
	person: tempPerson object
	passw:  string, the password to access the db carried over so the user doesn't have to enter it again
@returns:
	an array of tempMovie objects where the people categories are 'None'
	None if the actor does not exist in the database
"""
def portfolio(person, passw):
	conn = psycopg2.connect(database="test", user="postgres", password=passw, host="127.0.0.1", port="5432")
	global cur
	cur = conn.cursor()
	person_id = getPersonID(person)
	if person_id == None:
		return None
	if person.p_type == "actor":
		cur.execute("SELECT TITLE,YEAR,RUNTIME,MPAA,RATING,WATCHED,OWN,DIRECTORS.name from MOVIES, ACTORS, ACTING, DIRECTORS, DIRECTING WHERE ACTORS.id = " + str(person_id) + " AND MOVIES.id = ACTING.m_id AND ACTORS.id = ACTING.a_id AND MOVIES.id = DIRECTING.m_id AND DIRECTORS.id = DIRECTING.d_id")
	elif person.p_type == "director":
		cur.execute("SELECT TITLE,YEAR,RUNTIME,MPAA,RATING,WATCHED,OWN,DIRECTORS.name from MOVIES, DIRECTORS, DIRECTING WHERE DIRECTORS.id = " + str(person_id) + " AND MOVIES.id = DIRECTING.m_id AND DIRECTORS.id = DIRECTING.d_id")
	else:
		cur.execute("SELECT TITLE,YEAR,RUNTIME,MPAA,RATING,WATCHED,OWN,DIRECTORS.name from MOVIES, WRITERS, WRITING, DIRECTORS, DIRECTING WHERE WRITERS.id = " + str(person_id) + " AND MOVIES.id = WRITING.m_id AND WRITERS.id = WRITING.w_id AND MOVIES.id = DIRECTING.m_id AND DIRECTORS.id = DIRECTING.d_id")
	found_movies = []
	for row in cur.fetchall():
		new_movie = tempMovie(row[0], None, None, None, row[1], str(row[2]), row[3], str(row[4]), str(row[5]), str(row[6]))
		directors = []
		for i in range(7, len(row)):
			directors.append(row[i])
		new_movie.director = directors
		found_movies.append(new_movie)
		
	conn.close()
	return found_movies

"""
Returns all movies that the user hasn't watched.
@params:
	passw:  string, the password to access the db carried over so the user doesn't have to enter it again
@returns:
	an array of tempMovie objects 
"""
def getMoviesToWatch(passw):
	conn = psycopg2.connect(database="test", user="postgres", password=passw, host="127.0.0.1", port="5432")
	global cur
	cur = conn.cursor()
	cur.execute("SELECT TITLE,YEAR,RUNTIME,MPAA,RATING,WATCHED,OWN from MOVIES WHERE MOVIES.watched = FALSE")
	found_movies = []
	for row in cur.fetchall():
		found_movies.append(tempMovie(row[0], None, None, None, row[1], str(row[2]), row[3], str(row[4]), str(row[5]), str(row[6])))
	conn.close()
	return found_movies

"""
Checks for a duplicate of the movie object entered.
As of version 1.0, 2 movies with the same year and title cannot exist in the db.
@params:
	h_movie: tempMovie object, movie we are checking the db for.
@returns:
	False if no movie in the db matches h_movie
	True if match is found
"""
def hasMovie(h_movie):
	cur.execute("SELECT * from MOVIES WHERE title = " + "'" + h_movie.title + "' AND year = " +  "'" + h_movie.year + "'")
	result = cur.fetchall()
	if result != []:
		return True
	else: 
		return False

"""
Checks for a duplicate of the person object entered.
As of version 1.0, 2 people with the same name cannot exist in each table.
@params:
	h_person: tempPerson object, person we are checking the db for.
	passw:    string, the password to access the db carried over so the user doesn't have to enter it again
	orig:     boolean, True if this method is being called from myMDb, False if it is being called as a helper function
@returns:
	False if no person in the db matches h_person
	True if match is found
"""
def hasPerson(h_person, passw, orig):
	if orig:
		conn = psycopg2.connect(database="test", user="postgres", password=passw, host="127.0.0.1", port="5432")
		global cur
		cur = conn.cursor()
	if h_person.p_type == "actor":
		table = "ACTORS"
	elif h_person.p_type == "director":
		table = "DIRECTORS"
	else:
		table = "WRITERS"
	cur.execute("SELECT * from " + table + " WHERE name = '" + h_person.name + "'")
	result = cur.fetchall()
	if result != []:
		return True
	else:
		return False

"""
Finds the id of the desired movie in the MOVIES table.
@params:
	g_movie: tempMovie object
@returns:
	int id of the movie if it exists
	None if the movie is not in the db
"""
def getMovieID(g_movie):
	cur.execute("SELECT id from MOVIES WHERE title = " + "'" + g_movie.title + "' AND year = " +  "'" + g_movie.year + "'")
	result = cur.fetchall()
	if result != []:
		return result[0][0]

"""
Finds the id of the desired person in the ACTORS, DIRECTORS, or WRITERS table.
@params:
	g_person: tempPerson object
@returns:
	int id of the person if it exists
	None if the person is not in the db
"""
def getPersonID(g_person):
	if g_person.p_type == "actor":
		table = "ACTORS"
	elif g_person.p_type == "director":
		table = "DIRECTORS"
	else:
		table = "WRITERS"
	cur.execute("SELECT id from " + table + " WHERE name = '" + g_person.name + "'")
	result = cur.fetchall()
	if result != []:
		return result[0][0]

"""
Updates the data of a movie already in the database. Specifically user-generated info.
@params:
	u_movie: tempMovie object, the movie to updateMovie
	rating:  float, the new rating
	own:     boolean, the new own value
	watched: boolean, the new watched value
"""
def updateMovie(u_movie, rating, watched, own, passw):
	conn = psycopg2.connect(database="test", user="postgres", password=passw, host="127.0.0.1", port="5432")
	global cur
	cur = conn.cursor()
	u_id = getMovieID(u_movie)
	if own:
		own_string = "TRUE"
	else:
		own_string = "FALSE"
	if watched:
		watched_string = "TRUE"
	else:
		watched_string = "FALSE"
	cur.execute("UPDATE MOVIES SET RATING = " + rating + " WHERE ID = " + str(u_id))
	cur.execute("UPDATE MOVIES SET OWN = " + own_string + " WHERE ID = " + str(u_id))
	cur.execute("UPDATE MOVIES SET WATCHED = " + watched_string + " WHERE ID = " + str(u_id))
	conn.commit()
	conn.close()
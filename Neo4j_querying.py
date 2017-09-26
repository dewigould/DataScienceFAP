#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Contains snippets of part of a larger process. 

The below class contains methods to access a previously hydrated Neo4j Graph Database
and query it for the required information. In this instance: friend suggestions and 
nodes connected by common connections.

Invovles accessing the Neo4j Python Driver API
"""

from neo4j.v1 import GraphDatabase
import psycopg2

conn = psycopg2.connect("dbname=XXXX user=XXXXX host=XXXXXXX port=XXXXXX password=XXXXXXXXXXX")
uri = "XXXXXXX"
username = "XXXXX"
password = "XXXXXXX"

class queries:
    """
    Contains methods for stream-lining specific queries into one line of code.
    Methods should include get_friend_suggestions,get_invitable_friends etc.
    """
    def __init__(self,uri,username,password,session_id_input):
        self._uri = uri
        self._username = username
        self._password = password
        self._driver = GraphDatabase.driver(self._uri,auth=(self._username,self._password))
        self._session_id = session_id_input
        
    def get_friend_suggestions(self):

        print "Ordered list of friend suggestions: "
        print "Node 1, Node 2, Distance between nodes (smaller is better)"
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run("MATCH p = (s1:Session {Session_ID:{session_id}})-[r]-()-[r1]-(s2:Session)"
                       "CREATE (s1)-[r2:HAS_FRIEND_SUGGESTION]->(s2)"
                       "SET r2.Distance = r.Distance + r1.Distance",session_id = self._session_id)
                for record in tx.run("MATCH p=(s1:Session {Session_ID:{session_id}})-[rels]->(s2:Session) "
                                     "RETURN s1.Session_ID,s2.Session_ID, rels.Distance "
                                     "ORDER BY rels.Distance ASC "
                                     "LIMIT 100 ", session_id = self._session_id):
                    print record["s1.Session_ID"],record["s2.Session_ID"],record["rels.Distance"]
                    
    def finish_and_delete(self):
        """
        This should be called only when the user is absolutely finished with all queries
        It deletes the entire database and removes all indexes/ nodes/ edges.
        """
        conn.close()
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run("MATCH (n) DETACH DELETE n")
                tx.run("DROP INDEX ON :Session(Session_ID)")
                tx.run("DROP INDEX ON :FacebookContact(Facebook_ID)")
                tx.run("DROP INDEX ON :Group(Group_ID)")
                tx.run("DROP INDEX ON :Event(Event_ID)")
                tx.run("DROP INDEX ON :FriendGroup(Group_ID)")
 
    def close(self):
        """
        Should be the last method called - shuts access off to Neo4j Python Driver.
        """
        self._driver.close()
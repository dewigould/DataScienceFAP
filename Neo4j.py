#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Contains snippets of part of a larger process. 

The below class contains methods to generate nodes and edges in a Neo4j Graph Database
using previously obtained user data.

Invovles accessing the Neo4j Python Driver API
"""

from neo4j.v1 import GraphDatabase
import matplotlib.pyplot as plt
import numpy as np
import time


conn = psycopg2.connect("dbname=XXXX user=XXXXX host=XXXXXXX port=XXXXXX password=XXXXXXXXXXX")
uri = "XXXXXXX"
username = "XXXXX"
password = "XXXXXXX"


class Neo4j_hydration:
    
    def __init__(self,uri,username,password,session_id_input):
        self._uri = uri
        self._username = username
        self._password = password
        self._driver = GraphDatabase.driver(self._uri,auth=(self._username,self._password))
        self._session_id = session_id_input
    
    def index_session(self):
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run("CREATE INDEX ON :Session(Session_ID)")
                tx.run("CREATE INDEX ON :FacebookContact(Facebook_ID)")
                tx.run("CREATE INDEX ON :PhoneContact(Phone_Number)")
                tx.run("CREATE INDEX ON :Group(Group_ID)")
                tx.run("CREATE INDEX ON :Event(Event_ID)")
                tx.run("CREATE INDEX ON :FriendGroup(Group_ID)")
                tx.run("CREATE INDEX ON :InvitableFriend(Name)")
                tx.run("CREATE INDEX ON :FacebookTag(Name)")
                
    
    def hydrate_neo4j(self):
        """
        This method is no longer in use, but I have kept it in case.
        The above 'in stages' approach is much faster and is therefore used from now on
        however, if the size of edges required is small (ie. once the database is already hydrated) this could perhaps
        be a better and faster approach (it doesn't segmentise the process so would be faster for small enough sample size)
        """
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                print "Number of edges to add: ", len(self._edges)
                counter = 0
                for edge in self._edges:
                    node_1 = edge[0]
                    node_2 = edge[1]
                    info = edge[2]
                    
                    if node_2 == None:
                        start = time.time()
                        tx.run("CREATE (s:Session {Session_ID:{session_id}})",{"session_id":node_1})
                        end = time.time()
                        counter +=1
                        self._timing.append(end-start)
                        self._x.append(counter)


                    elif info["Type Node 2"] == "Phone Number":
                        start = time.time()
                        tx.run("MERGE (p:PhoneContact {Phone_Number:{phone_number}})",{"phone_number":node_2})
                        tx.run("MATCH (s:Session),(p:PhoneContact)"
                               "WHERE s.Session_ID = {session_id} AND p.Phone_Number = {phone_number}"
                               "CREATE (s)-[:HAS_PHONE_NUMBER {Distance:toInt({distance})}]->(p)",{"session_id":node_1,"phone_number":node_2,"distance":info["Distance"]})
                        counter +=1 
                        end = time.time()
                        if (end-start) >0.1:
                            print (end-start)

                    elif info["Type Node 2"] == "Facebook ID":
                            
                        start = time.time()
                        tx.run("MERGE (p:FacebookContact {Facebook_ID:{facebook_id}})",{"facebook_id":node_2})
                        tx.run("MATCH (s:Session),(p:FacebookContact)"
                               "WHERE s.Session_ID = {session_id} AND p.Facebook_ID = {facebook_id}"
                               "CREATE (s)-[:HAS_FACEBOOK_ID {Distance: toInt({distance})}]->(p)",{"session_id":node_1,"facebook_id":node_2,"distance":info["Distance"]})
                               
                        counter +=1 
                        end= time.time()
                        if (end-start) >1:
                            print (end-start)
                        self._timing.append(end-start)
                        self._x.append(counter)

                    elif info["Type Node 2"] == "Phone Contact":
                        start = time.time()
                        tx.run("MERGE (p:PhoneContact {Phone_Number:{phone_number}})",{"phone_number":node_2})
                        tx.run("MATCH (s:Session),(p:PhoneContact)"
                               "WHERE s.Session_ID = {session_id} AND p.Phone_Number = {phone_number}"
                               "CREATE (s)-[:HAS_PHONE_CONTACT {Distance: toInt({distance})}]->(p)", {"session_id":node_1,"phone_number":node_2,"distance":info["Distance"]})
                        counter +=1
                        end = time.time()
                        if (end-start) >0.1:
                            print (end-start)

                    elif info["Type Node 2"] == "Facebook Contact":

                        start = time.time()

                        tx.run("MERGE (p:FacebookContact {Facebook_ID:{facebook_id}})",{"facebook_id":node_2})
                        tx.run("MATCH (s:Session),(p:FacebookContact)"
                               "WHERE s.Session_ID = {session_id} AND p.Facebook_ID = {facebook_id}"
                               "CREATE (s)-[:HAS_FACEBOOK_CONTACT {Distance: toInt({distance})}]->(p)",{"session_id":node_1,"facebook_id":node_2,"distance":info["Distance"]})
                                                      
                        counter +=1 
                        end = time.time()
                        if (end-start) >1:
                            print (end-start)
                        self._timing.append(end-start)
                        self._x.append(counter)

                    elif info["Type Node 2"] == "Group":
                        if info["Type Edge"] == "MEMBER_OF_GROUP":
                            tx.run("MATCH (s:Session {Session_ID:{session_id}})"
                                   "MERGE (p:Group {Group_ID:{group_id}})"
                                   "CREATE (s)-[:MEMBER_OF_GROUP {Distance: toInt({distance})}]->(p)", {"session_id":node_1,"group_id":node_2,"distance":info["Distance"]})                        
                            counter +=1
                        if info["Type Edge"] == "MEMBER_OF_FRIEND_GROUP":
                            tx.run("MATCH (s:Session {Session_ID:{session_id}})"
                                   "MERGE (p:FriendGroup {Group_ID:{group_id}})"
                                   "CREATE (s)-[:MEMBER_OF_Friend_GROUP {Distance: toInt({distance})}]->(p)", {"session_id":node_1,"group_id":node_2,"distance":info["Distance"]})        
                            counter +=1
                            
                    elif info["Type Node 2"] == "Event":                                      
                            tx.run("MATCH (s:Session {Session_ID:{session_id}})"
                                   "MERGE (p:Event {Event_ID:{event_id}})"
                                   "CREATE (s)-[:PARTICIPATED_IN {Distance: toInt({distance})}]->(p)", {"session_id":node_1,"event_id":node_2,"distance":info["Distance"]})        
                            counter +=1
                            
                    elif info['Type Node 2'] == "Invitable_Friend":
                        tx.run("MATCH (s:Session {Session_ID:{session_id}})"
                               "MERGE (f:InvitableFriend {Name: {name}})"
                               "CREATE (s)-[:HAS_INVITABLE_FACEBOOK_FRIEND {Distance:toInt({distance})}]->(f)",{"session_id":node_1,"name":node_2,"distance":info["Distance"]})
                        counter +=1
                    elif info["Type Node 2"] == "Facebook_Tag":
                        tx.run("MATCH (s:Session {Session_ID:{session_id}})"
                               "MERGE (f:FacebookTag {Name: {name}})"
                               "CREATE (s)-[:TAGGED_IN_FACEBOOK_PHOTO {Distance:toInt({distance})}]->(f)",{"session_id":node_1,"name":node_2,"distance":info["Distance"]})
                        counter +=1
                        
                    if counter in [5000,10000,15000,20000,25000,50000,100000,200000,300000,400000,500000,600000,750000,1000000,1100000,1200000,1300000,1400000,1500000,175000002000000]:
                        print counter
    
    def timing(self):
        """
        Yield plot on time of each Neo4j iteration (ie. each individual query)
        This was initially built to explore the possible flaws in the upload process
        """
        plt.plot(self._x,self._timing,color = 'blue')
        plt.plot(self._x,[np.mean(self._timing) for i in self._timing],color='red')
        plt.xlabel("Iteration")
        plt.ylabel("Time taken for iteration (seconds)")
        plt.show()
        
    def show_graph(self):
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run("MATCH(n) return n limit 25")
                
    def finish_and_delete(self):
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
        self._driver.close()
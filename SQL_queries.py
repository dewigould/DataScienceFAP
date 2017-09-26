#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This scrip contains snippets of a larger code. This represents the first set of methods used in a longer process
Data is collected from PostgreSQL database and sorted into weighted edges with various attributes.
This is for implementing into a Graph Database later on.
"""
from collections import defaultdict
import psycopg2



conn = psycopg2.connect("dbname=XXXX user=XXXXX host=XXXXXXX port=XXXXXX password=XXXXXXXXXXX")
uri = "XXXXXXX"
username = "XXXXX"
password = "XXXXXXX"

class Edges:
    
    """
    Contains methods to collect data from Postgresql and generate 'edges' 
    For example, edges are created if a user has played with a certain group, or in a certain event.

        (SESSION)-[:PARTICIPATED IN {DISTANCE: NUMBER OF PARTICIPANTS}]->(EVENT)
        (SESSION)-[:IS MEMBER OF GROUP {DISTANCE: NUMBER OF MEMBERS}]->(GROUP)
        (SESSION)-[:IS MEMBER OF FRIEND GROUP {DISTANCE:0}]->(GROUP)
    """ 
    
    def __init__(self,uri,username,password,session_id_input):
        self._uri = uri
        self._username = username
        self._password = password

        self._edges = []
        self._number_facebook_contacts = defaultdict(lambda:0)
        self._number_phone_contacts = defaultdict(lambda:0)
        self._number_group_members = defaultdict(lambda:0)
        self._number_event_participants = defaultdict(lambda:0)

        
        self._session_id = str(session_id_input)
        
    def wipe(self):
        self._edges = []
       
    def chunkify(self,list_edges,n):
        return [list_edges[i::n] for i in xrange(n)]
    
    def split_up(self):
        length = len(self._edges)
        if length != 0 :
            self._split_up_edges = self.chunkify(self._edges,100)
        
    def hydrate_sessions(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        sessions.id
        FROM sessions
        """)
        out = cur.fetchall()
        print "Number of Sessions: ", len(out)
        for i in out:
            self._edges.append((i[0],None,{"Type Node 1": "Session", "Type Node 2":None}))
        
    def hydrate_phone(self):
        self.get_number_phone_contacts()
        cur = conn.cursor()
        cur.execute("""SELECT
        phone_numbers.phone_number,
        phone_numbers.id,
        contact_book_items_phone_numbers.phone_number_id,
        contact_book_items.contact_book_id,
        contact_books.session_id
        FROM phone_numbers
        INNER JOIN contact_book_items_phone_numbers ON contact_book_items_phone_numbers.phone_number_id = phone_numbers.id
        INNER JOIN contact_book_items ON contact_book_items.id = contact_book_items_phone_numbers.contact_book_item_id
        INNER JOIN contact_books ON contact_books.id = contact_book_items.contact_book_id
        """)
        out = cur.fetchall()
        print "Number of Phone connections: ", len(out)
        cur.close()
        for i in out:  
            self._edges.append((i[4],i[0],{"Type Node 1":"Session", 'Type Node 2': "Phone Contact","Distance": self._number_phone_contacts[i[4]] ,"Type Edge":"HAS_PHONE_CONTACT"}))
        self.include_phone_number_connections()

    def hydrate_facebook_contacts(self):
        self.get_number_facebook_contacts()
        cur = conn.cursor()
        cur.execute("""SELECT
        contact_books.session_id,
        sessions.facebook_id,
        facebook_connections.facebook_id,
        contact_book_items_facebook_connections.facebook_connection_id,
        contact_book_items_facebook_connections.id
        FROM contact_book_items
        INNER JOIN contact_book_items_facebook_connections
        ON contact_book_items.id = contact_book_items_facebook_connections.contact_book_item_id
        INNER JOIN facebook_connections
        ON contact_book_items_facebook_connections.facebook_connection_id = facebook_connections.id
        INNER JOIN contact_books ON contact_book_items.contact_book_id = contact_books.id
        INNER JOIN sessions ON contact_books.session_id = sessions.id
        """)
        out = cur.fetchall()
        print "Number of Facebook Contacts: ", len(out)
        cur.close()
        for i in out:
            self._edges.append((i[0],i[2],{"Type Node 1":"Session","Type Node 2":"Facebook Contact","Facebook ID":i[2],"Distance":self._number_facebook_contacts[i[0]],"Type Edge":"HAS_FACEBOOK_CONTACT"}))
        self.include_facebook_id_connections()

    
    def hydrate_group_membership(self):
        self.get_number_members_of_group()
        cur = conn.cursor()
        cur.execute("""SELECT 
        group_members.session_id,
        group_members.group_id,
        groups.name
        FROM group_members
        INNER JOIN groups on groups.id = group_members.group_id
        """)
        out = cur.fetchall()
        print "Number of Group Connections: ", len(out)
        cur.close()
        for i in out:
            if "friends_user_group" not in i[2] and i[0] != None:
                self._edges.append((i[0],i[1],{"Type Node 1":"Session", "Type Node 2": "Group","Distance":self._number_group_members[i[1]],"Type Edge":"MEMBER_OF_GROUP"}))
            elif i[0] != None:
                self._edges.append((i[0],i[1],{"Type Node 1": "Session", "Type Node 2":"Group","Distance":0,"Type Edge":"MEMBER_OF_FRIEND_GROUP"}))
        
    def hydrate_event_participation(self):
        self.get_number_of_event_participants()
        cur = conn.cursor()
        cur.execute("""SELECT
        event_participants.session_id,
        event_participants.event_id
        FROM event_participants
        """)
        out = cur.fetchall()
        print "Number of Event participation connecitons: ", len(out)
        cur.close()
        for i in out:
            if i[0] != None:
                self._edges.append((i[0],i[1],{"Type Node 1": "Session","Type Node 2":"Event","Distance": self._number_event_participants[i[1]],"Type Edge":"PARTICIPATED_IN"}))
    
    def include_phone_number_connections(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        contact_details.session_id,
        contact_details.value
        FROM contact_details
        WHERE contact_details.key = 'phone_number'
        """)
        out = cur.fetchall()
        cur.close()
        for i in out:
            self._edges.append((i[0],i[1],{"Type Node 1":"Session","Type Node 2":"Phone Number", "Type Edge": "HAS_PHONE_NUMBER","Distance":0}))
        print "Number of Phone Number connections", len (out)
        
    def include_facebook_id_connections(self):
        
        cur = conn.cursor()
        cur.execute("""SELECT
        sessions.facebook_id,
        sessions.id
        FROM sessions 
        """)
        out = cur.fetchall()
        print "Number of Facebook ID connections ", len(out)
        cur.close()
        for i in out:
            self._edges.append((i[1],i[0],{"Type Node 1":"Session","Type Node 2":"Facebook ID", "Type Edge":"HAS_FACEBOOK_ID","Distance":0}))
    
    def get_number_of_event_participants(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        event_participants.session_id,
        event_participants.event_id
        FROM event_participants
        """)
        out = cur.fetchall()
        for i in out:
            self._number_event_participants[i[1]] +=1
        cur.close()

    def get_number_members_of_group(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        group_members.session_id,
        group_members.group_id
        FROM group_members
        """)
        out = cur.fetchall()
        for i in out:
            self._number_group_members[i[1]] +=1
        cur.close()
             
    def get_number_phone_contacts(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        contact_books.session_id,
        contact_book_items.name,
        contact_book_items.id,
        contact_book_items_phone_numbers.phone_number_id,
        phone_numbers.phone_number
        FROM contact_book_items
        INNER JOIN contact_books ON contact_book_items.contact_book_id = contact_books.id
        INNER JOIN contact_book_items_phone_numbers
        ON contact_book_items.id = contact_book_items_phone_numbers.contact_book_item_id
        INNER JOIN phone_numbers ON phone_numbers.id = contact_book_items_phone_numbers.phone_number_id
        """)
        out = cur.fetchall()
        for i in out:
            self._number_phone_contacts[i[0]] +=1
        cur.close()        
    
    def get_number_facebook_contacts(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        contact_books.session_id,
        sessions.facebook_id,
        facebook_connections.facebook_id,
        contact_book_items_facebook_connections.facebook_connection_id,
        contact_book_items_facebook_connections.id
        FROM contact_book_items
        INNER JOIN contact_book_items_facebook_connections
        ON contact_book_items.id = contact_book_items_facebook_connections.contact_book_item_id
        INNER JOIN facebook_connections
        ON contact_book_items_facebook_connections.facebook_connection_id = facebook_connections.id
        INNER JOIN contact_books ON contact_book_items.contact_book_id = contact_books.id
        INNER JOIN sessions ON contact_books.session_id = sessions.id
        """)
        out = cur.fetchall()
        cur.close()   
        for i in out:
            self._number_facebook_contacts[i[0]] +=1
    
    def get_edges(self):
        return self._edges
    
    def facebook_id(self):
        self.assign_facebook_ID()
        return self._Facebook_ID
    
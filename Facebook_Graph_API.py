#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Contains snippet of a larger process.

This script follows the below logic:
    
    Scour user data to obtain Facebook OAuth Access Token
    Use access token to access Facebook Graph API
    Find Facebook Friends and Facebook Tags by said user
    Generate "edges" with a mathematical weight and graph attributes
    
This invovles accessing the Facebook Graph API 
    
"""

from collections import defaultdict, Counter
import psycopg2,ast,json,requests



conn = psycopg2.connect("dbname=XXXX user=XXXXX host=XXXXXXX port=XXXXXX password=XXXXXXXXXXX")
uri = "XXXXXXX"
username = "XXXXX"
password = "XXXXXXX"


class Facebook_Edges():
    
    """
    Contains methods to collect data from Postgresql and Facebook Graph API and generate 'edges' 
    For example, edges are created if a user has a Facebook friend, or has tagged someone on Facebook

        example edge:
            
        (SESSION)-[:HAS FACEBOOK FRIEND {DISTANCE: CALCULATED WEIGHTING BASED ON STRENGTH OF 'FRIENDSHIP'}]->(FRIEND)
    """ 
    
    def __init__(self,uri,username,password,session_id_input):
        
        self._uri = uri
        self._username = username
        self._password = password
        
        self._session_id = str(session_id_input)
        self._OAuth_token = None
        self._Facebook_ID = None
        self._OAuth_list = defaultdict(lambda: None)

    def get_edges(self):
        return self._edges
    
    def facebook_id(self):
        self.assign_facebook_ID()
        return self._Facebook_ID
    
    def OAuth_token(self):
        self.assign_OAuth_token()
        return self.OAuth_token    
    
    
    def hydrate_invitable_friends(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        session_preferences.session_id,
        session_preferences.key,
        session_preferences.value
        FROM session_preferences        
        """)
        out = cur.fetchall()
        for i in out:
            if i[1] == "facebook_oauth_access_token":
                self._OAuth_list[i[0]] = i[2]

        for i in self._OAuth_list.items():
            list_names = []

            facebook_id = self.assign_facebook_ID_from_token(i[2])
            info = self.load_information_from_link(self.access_invitable_friends_all(facebook_id,i[1]))                
        
            if info != None:
                if u'invitable_friends' in info.keys():
                    for i in info[u'invitable_friends'][u'data']:
                        if u'name' in i.keys():
                            list_names.append(i[u'name'].encode('utf8'))
                    if u'paging' in info[u'invitable_friends'].keys():
                        for i in self.pagination(info[u'invitable_friends'],"invitables"):
                            list_names.append(i)
            print "number of facebook invitable friends", len(list_names)
            for j in list_names:
                self._edges.append((i[0],j,{"Distance":len(list_names),"Type Node 1":"Session","Type Node 2":"Invitable_Friend","Type Edge":"HAS_FACEBOOK_INVITABLE_FRIEND"}))
                
                
    def hydrate_facebook_tags(self):
        cur = conn.cursor()
        cur.execute("""SELECT
        session_preferences.session_id,
        session_preferences.key,
        session_preferences.value
        FROM session_preferences        
        """)
        out = cur.fetchall()
        for i in out:
            if i[1] == "facebook_oauth_access_token":
                self._OAuth_list[i[0]] = i[2]
        for i in self._OAuth_list.items():
            list_tags = []
            facebook_id = self.assign_facebook_ID_from_token(i[2])
            info = self.load_information_from_link(self.access_facebook_tags_all(facebook_id,i[1]))
       
            if info != None:
                if u'photos' in info.keys():
                    for i in info[u'photos'][u'data']:
                        if u'tags' in i.keys():
                            for j in i[u'tags'][u'data']:
                                if u'id' in i.keys():
                                    list_tags.append((i[u'name'].encode('utf8'),{"Facebook ID":i[u'id']}))
                                else:
                                    list_tags.append(i[u'name'].encode('utf8'))
                    if u'paging' in i[u'photos'].keys():
                        for i in self.pagination(info[u'photos'],"tags"):
                            list_tags.append(i)
            print "number of facebook tags", len(list_tags)
            c = Counter(list_tags)
            for j in list_tags:
                if type(i) == tuple:
                    self._edges.append((i[0],j[0],{"Distance":len(list_tags)/float(c[i]),"Type Node 1":"Session","Type Node 2":"Facebook_Tag","Type Edge":"TAGGED_IN_PHOTO"}))
                else:
                    self._edges.append((i[0],j,{"Distance":len(list_tags)/float(c[i]),"Type Node 1":"Session","Type Node2 ":"Facebook_Tag","Type Edge":"TAGGED_IN_PHOTO"}))
            
  
    def assign_OAuth_token(self):
        #obtain Facebook OAuth access token from database to access information through Graph Database.
        cur = conn.cursor()
        cur.execute("""SELECT
        session_preferences.session_id,
        session_preferences.key,
        session_preferences.value
        FROM session_preferences
        WHERE session_preferences.session_id = {0}
        """.format(self._session_id))
        out = cur.fetchall()
        cur.close()
        for i in out:
            if i[1] == "facebook_oauth_access_token":
                self._OAuth_token = i[2]
       
    def access_link(self,link):
        r = requests.get(link)
        information = r.text
        return information
    
    def load_information_from_link(self,output):
        if output!= None:
            return json.loads(output)
        else:
            return None    
    def assign_facebook_ID_from_token(self,token):
        link = "https://graph.facebook.com/me?access_token={}".format(token)
        information_raw = self.access_link(link)
        information = ast.literal_eval(information_raw.encode('utf8'))
        if "error" not in information.keys():
            return information["id"]
        
    def assign_facebook_ID(self):
        #get Facebook ID required for searching Graph Database.
        link = "https://graph.facebook.com/me?access_token={}".format(self._OAuth_token)
        information_raw = self.access_link(link)
        information = ast.literal_eval(information_raw.encode('utf8'))
        if "error" not in information.keys():
            self._Facebook_ID = information["id"]
    
    def access_invitable_friends_all(self,facebook_id,OAuth_token):
        if facebook_id != None:
            link = "https://graph.facebook.com/{0}?fields=name,id,invitable_friends&access_token={1}".format(facebook_id,OAuth_token)
            information = self.access_link(link)
            return information
        else:
            return None
        
    def access_invitable_friends(self):
        #intermediate step to obtaining list of Facebook invitable friends to add into Neo4j network for path analysis.
        if self._Facebook_ID != None:
            link = "https://graph.facebook.com/{0}?fields=name,id,invitable_friends&access_token={1}".format(self._Facebook_ID,self._OAuth_token)
            information = self.access_link(link)
            return information
        else:
            return None
    
    def get_list_invitables(self):
        #obtain list of invitable friends for adding to Neo4j later.
        self.assign_OAuth_token()
        self.assign_facebook_ID()
        list_names = []
        info = self.load_information_from_link(self.access_invitable_friends())
        if info != None:
            if u'invitable_friends' in info.keys():
                for i in info[u'invitable_friends'][u'data']:
                    if u'name' in i.keys():
                        list_names.append(i[u'name'].encode('utf8'))
            if u'paging' in info[u'invitable_friends'].keys():
                    for i in self.pagination(info[u'invitable_friends'],"invitables"):
                        list_names.append(i)
        print "number of facebook invitable friends", len(list_names)
        for i in list_names:
            self._edges.append((self._session_id,i,{"Distance":len(list_names),"Type Node 1":"Session","Type Node 2":"Invitable_Friend","Type Edge":"HAS_FACEBOOK_INVITABLE_FRIEND"}))
    
    def pagination(self,information,key):
        # 'information' is that gathered from Facebook Graph API
        #key is 'invitables' or 'tags' - slightly interferes with way pages are examined
        friends = []
        counter = 0
        thing = information
        while counter <=10: #only look at first 10 pages to keep numbers sensible.
            if u'paging' in thing.keys():
                if u'next' in thing[u'paging'].keys():
                    new_thing = self.load_information_from_link(self.access_link(thing[u'paging'][u'next'].encode('utf8')))
                    if new_thing != None:
                        if u'data' in new_thing.keys():
                            for i in new_thing[u'data']:
                                if u'name' in i.keys():
                                    if key == "invitables":
                                        friends.append(i[u'name'].encode('utf8'))
                                    if key == "tags":
                                        if u"id" in i.keys():
                                            friends.append((i[u'name'].encode('utf8'),{"Facebook ID": i[u'id']}))
                                        else:
                                            friends.append(i[u'name'].encode('utf8'))
                        if u'paging' in new_thing.keys():
                            thing = new_thing
                            counter +=1
                        else: 
                            counter = 100
                            thing = {}
                    else:
                        counter = 100 
                        thing={}
                else:
                    counter = 100
                    thing = {}                 
        return friends  
    
    def access_facebook_tags_all(self,facebook_id,OAuth_token):
        if facebook_id != None:
            link = "https://graph.facebook.com/{}?fields=name,id,photos{}&access_token{}".format(facebook_id,"{tags{name}}",OAuth_token)
            r = requests.get(link)
            return r.text
        else:
            return None
    def access_facebook_tags(self):
        if self._Facebook_ID != None:
            link = "https://graph.facebook.com/{}?fields=name,id,photos{}&access_token{}".format(self._Facebook_ID,"{tags{name}}",self._OAuth_token)
            r= requests.get(link)
            return r.text
        else:
            return None
        
    def get_list_tags(self):

        self.assign_OAuth_token()
        self.assign_facebook_ID()
        list_tags = []
        info = self.load_information_from_link(self.access_facebook_tags())
        if info != None:
            if u'photos' in info.keys():
                for i in info[u'photos'][u'data']:
                    if u'tags' in i.keys():
                        for j in i[u'tags'][u'data']:
                            if u'id' in i.keys():
                                list_tags.append((i[u'name'].encode('utf8'),{"Facebook ID":i[u'id']}))
                            else:
                                list_tags.append(i[u'name'].encode('utf8'))
                if u'paging' in i[u'photos'].keys():
                    for i in self.pagination(info[u'photos'],"tags"):
                        list_tags.append(i)
        print "number of facebook tags", len(list_tags)
        c = Counter(list_tags)
        for i in list_tags:
            if type(i) == tuple:
                self._edges.append((self._session_id,i[0],{"Distance":len(list_tags)/float(c[i]),"Type Node 1":"Session","Type Node 2":"Facebook_Tag","Type Edge":"TAGGED_IN_PHOTO"}))
            else:
                self._edges.append((self._session_id,i,{"Distance":len(list_tags)/float(c[i]),"Type Node 1":"Session","Type Node2 ":"Facebook_Tag","Type Edge":"TAGGED_IN_PHOTO"}))
    
    
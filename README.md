# DataScienceFAP
Includes snippets of codes and methods written as part of data science internship at FindaPlayer.

The majority of important SQL and CYPHER queries have been marked XXXXXX to be kept private. 

The purpose of this repository is to show the general techinques and progamming skills I used and developed as part of this internship.

### It is important to note that all of the below scripts are simply chunks of a larger code that have been split up to the process. They are therefore not functional as stand alone scripts.

## Overview

# SQL Queries of PostgreSQL database
* SQL_Queries.py
This script shows some small methods which demonstrate how I used SQL Queries to access database information.

# Accessing and using information from Facebook Graph API
* Facebook_Graph_API.py
This script shows some small methods which show how I accessed Facebook Graph API and queried it to obtain information pertinent to the next step of my work.

# Neo4j
## Using Neo4j Python Driver to generate and hydrate a Graph Database
* Neo4j.py
Use Neo4j Python Driver to create nodes and edges based on information created in other scripts from PostgreSQL database.

## CYPHER queries to access complete Graph Database to obtain required results
* Neo4j_querying.py
Once the Graph Database has been fully hydrated, this script provides quick methods to accessing the required information via CYPHER queries.

# Basic Graph building in NetworkX
* faster_phonenumbers.ipynb
Shows a very elementary use of NetworkX Python lib in order to analyse phone book information obtained from database. This script alows contains some experiments with projected networks and analysis of specific network properties.

# Key Word Search of public Facebook events
* PUBLIC_EVENTS.ipynb
This script is a rough guidline to the process I used to search Facebooks accessible due to the fact that their privacy settings are "public". I created a key-word search based on entries in the PostgreSQL database and sifted entries on Facebook to find strong matches. This was in an attempt to improve Facebook advertising.

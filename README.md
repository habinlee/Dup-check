# Dup-check

Outline
This service is a newly added function to the Crowdworks next generation crowd sourced data production platform. It detects reduplication of image/text data that the platform users have submitted by storing each data in GCP Datastore and comparing newly added data to the originally recorded data. Its purpose is to prevent fraudulent usage of the service and keep the financial rewards of every project fair.

Environment
- Google App Engine
    - Project : crowdworks-platform
    - Service : cw-dup-check
    - Runtime : Python37
    - Version : v5
- Google Datastore
    - Kind : dupcheck
    - Columns : Data_ID, Hash_Value, Project_ID, Timestamp, User_ID 

Function
- Using the GET method, receives parameters of image/text data from the URL and runs a reduplication check process returning a certain result in json format
- Data storage route and form : URL -> GCP Datastore
- Parameter information :
    - h [Hash_Value] : Image files give hash values, text files give the text itself -> essential parameter
    - p [Project_ID] : project ID of the applicable project
    - u [User_ID] : User ID that submitted the data
    - d [Data_ID] : the position value of the data submitted
    - mode : ‘r’ for read-only, ‘w’ for using the whole service (including write function)
- Using the information given by parameters, after the reduplication checking process if there are duplicate data, maximum of 5 items that have the same hash value are returned in json format
- Applied data security configuration using token, cors_allow_origin, header referer information from the http header

Sequence Diagram
![sequenc_diagram](https://user-images.githubusercontent.com/88265967/127762525-07c26d9d-fa07-45a7-8669-082a2ea5cc88.png)

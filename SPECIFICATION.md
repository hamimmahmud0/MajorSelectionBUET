In 4th year of BUET civil engineering department. The course is divided into 4 specialities: Structure, Transport, Environment and Geotech in short (S T E G). Undergraduate civil engineering student of Bangladesh University of Engineering and Technologies has to select two of the devisions among for. One is called Major and one is called minor. The difference between major and minor is that student has to complete in major division. The students that has to select supervisor under home they will perform thesis.

Problem is that each combination (major + minor) has a fixed amount of seats. Again each supervisor will take a fixed amount of students under him. The list of which supervisor will take how many student will be given. In formation is like:


list one:
|Major|Supervisor|seat|
|---|---|---|
|S|Amanat sir|4|
|S|Tahsin sir|4|
|T|Shamsul sit|4|

... so on

The list of Which major minor combination will have how many seats will also be given:

list two:
ST 27
SG 27
SE 27
TS 13
TE 13
TS 10

... so on


Ranking off student will may not be given but will be updated later by admin.
student id format: last two digit of intake year, two dept code, three digit roll 
Example: 2104065


year: 21
dept code: 04
roll: 065


The merit list of student ranking will be uploaded by admin in csv file as:


list 3:
```
1,2104043 
2,2104053
3,2104122
... so on
```

Or admin may upload it mannually in admin control panel.

Develop a website where students will be able to select there major minor preference priority list and super visor priority list. Students may not need to upload priority list for all combination. Suppose there 12 combination if student gave a list upto 6 assume remaining combinations has equal preference to that student.

The purpose of the website is to show which student will get which combination and supervisor. If student with higher rank prefers a combination and a supervisor it is more likely that students of lower rank will not get that combination or supervisor.

The website will contain:

1. Login page which takes student id
    Login page will contain a field for student id. If student id is new create a new account and add a filed to set password. After succesfully setting password and creating account route him to dashboard. 
    If account aleady exists authenticate and route to dashboard.
2. A admin page which requires username and password
    Admin will be able to add modify edit list one, two and three. Set number of students available. Change password of any account. The tables should be updated and dwonloaded in csv file if necessary.

3. A Dashborad page will show realtime list
    three section:
    - a section to show users current postion, The combination he will get according to current information, and supervisor he will get.
    - A section to select combination prioity list. List should be interactive and have dropdown features. No mannual typing shouldn't be required as admin panel will upload all necessary information. Also For every major he selected There should be a selection tool for supervisor priorites list.
    - A table view to show which student will get which Combination and Supervisor according sorting according to student id. A realtime search will filed will be there to filter student id and Combinations (a serach filed for filter value and a dropdown button for filter type. There should be search suggestion)


Use python + flask + tailwind save that data to sqlite so that it is recoverable.
This is the codebase for our project for inexact matching on music files with the goal of plagirism detection.

The files are separated by use.

Directory_Manger.h/.cpp: These are the files used to navigate the directories, extract the relavant files, and parse the json. 
They also do a little bit of pre-processing and build the database string we used for the alignment scores

Alignment.h/.cpp: This is the file that contains all of the different global and local alignment strategies we used. These include
the global Needleman-Wunsch, naive Smith-Waterman, parallel Smith-Waterman, and linear space Smith-Waterman

json.h: This was a header file necessary to use the nlohmann json parsing in C++

584_final.cpp: This was the main file that ran the project and defined the sigma function we used for alignment.

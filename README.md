This is the codebase for our project for inexact matching on music files with the goal of plagiarism detection.

The files are separated by use.

Under the preprocessing folder we have essential tasks such as additional deduplication of songs (584A Project Preprocessing with Copy), track filtering heuristics (584A Output JSON Interval Pitch Differences), and reading of track data in both a chroma encoded format and pitch interval based format (584A Output ngram JSON files) , along with an implementation of supermaximal repeats (584A Output ngram JSON files) which could be adapted to compared notable motifs between songs. Additionally, there was an attempt made to implement the TPS structure by Haas, and the small lightweight implementation of DTW for our case study.

Directory_Manger.h/.cpp: These are the files used to navigate the directories, extract the relavant files, and parse the json. They also do a little bit of pre-processing and build the database string we used for the alignment scores

Alignment.h/.cpp: This is the file that contains all of the different global and local alignment strategies we used. These include the global Needleman-Wunsch, naive Smith-Waterman, parallel Smith-Waterman, and linear space Smith-Waterman

json.h: This was a header file necessary to use the nlohmann json parsing in C++

584_final.cpp: This was the main file that ran the project and defined the sigma function we used for alignment.

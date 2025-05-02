#pragma once
#include <vector>
#include <iostream>
#include <limits>
#include <functional>
#include <algorithm>
#include "Directory_Manager.h"

using namespace std;

struct coord {
	int x;
	int y;
	coord(int xc, int yc): x(xc), y(yc) {}
};

//placeholder alphabet size 12
enum alphabet {
	a, b, c, d, e, f, g, h, i, j, k, l
};

//global alignment from top left to bottom right
vector<coord> needleman_wunsch(vector<alphabet> Q, vector<alphabet> T, int g, std::function<int(alphabet, alphabet)> sigma, int& score);

vector<coord> smith_waterman(vector<char> Q, vector<char> T, int g, std::function<int(char, char)> sigma, int& score, std::map<interval, json_identifer>find_song);

int smith_waterman_linear(vector<char> Q, vector<char> T, int g, std::function<int(char, char)> sigma, int& score, std::map<interval, json_identifer>find_song);

vector<coord> parallel_smith_waterman(vector<char> Q, vector<char> T, int g, std::function<int(char, char)> sigma, int& score);

/*
vector<coord> global_hirschberg(vector<alphabet> Q, vector<alphabet> T, int g, std::function<int(alphabet, alphabet)> sigma, int& score);

vector<coord> helper_hirschberg(vector<alphabet> Q, vector<alphabet> T, int g, std::function<int(alphabet, alphabet)> sigma, int& score);
*/
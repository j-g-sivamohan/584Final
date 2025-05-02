#include <vector>
#include <iostream>
#include <algorithm>
#include <omp.h>
#include <ctime>
#include "Alignment.h"

using namespace std;

vector<coord> needleman_wunsch(vector<alphabet> Q, vector<alphabet> T, int g, std::function<int(alphabet, alphabet)> sigma, int& score) {
	//set up the table
	std::vector<std::vector<int>> DPT(Q.size()+1, std::vector<int>(T.size()+1, 0));
	DPT[0][0] = 0;
	for (int i = 0; i < DPT[0].size(); i++) {
		DPT[0][i] = -1 * i * g;
	}
	for (int i = 0; i < DPT.size(); i++) {
		DPT[i][0] = -1 * i * g;
	}

	//fill the table
	for (int i = 0; i < DPT.size(); i++) {
		for (int j = 0; j < DPT[0].size(); j++) {
			int top = std::numeric_limits<int>::lowest();
			int left = std::numeric_limits<int>::lowest();
			int top_left = std::numeric_limits<int>::lowest();
			if (i > 0) {
				top = DPT[i - 1][j] - g;
			}
			if (j > 0) {
				left = DPT[i][j - 1] - g;
			}
			if (i > 0 && j > 0) {
				top_left = DPT[i - 1][j - 1] + sigma(Q[i-1],T[j-1]);
			}
			DPT[i][j] = max({ top,left,top_left });
		}
	}

	//reconstruct path
	int x = Q.size();
	int y = T.size();
	vector<coord> path;
	path.push_back(coord(Q.size(), T.size()));
	while (x > 0 || y > 0) {
		int top = std::numeric_limits<int>::lowest();
		int left = std::numeric_limits<int>::lowest();
		int top_left = std::numeric_limits<int>::lowest();
		if (x > 0) {
			top = DPT[x - 1][j];
		}
		if (y > 0) {
			left = DPT[i][y - 1];
		}
		if (x > 0 && y > 0) {
			top_left = DPT[x - 1][y - 1];
		}
		if (top > left && top > top_left) {
			path.push_back(coord(x - 1, y));
		}
		else if (left > top && left > top_left) {
			path.push_back(coord(x, y - 1));
		}
		else {
			path.push_back(coord(x - 1, y - 1));
		}
	}

	score = DPT[Q.size()][T.size()];

	return path;

}

vector<coord> smith_waterman(vector<char> Q, vector<char> T, int g, std::function<int(char, char)> sigma, int& score, std::map<interval, json_identifer>find_song) {
	std::vector<std::vector<short>> DPT(Q.size() + 1, std::vector<short>(T.size() + 1, 0));

	//no need for initialization because values should start at 0 in this case

	//need to track largest single cell in table as we go
	int best_x = 0;
	int best_y = 0;
	int best_value = 0;


	std::cout << "T size: " << T.size() << endl;

	//fill the table
	auto start_time = std::time(0);
	int top = std::numeric_limits<int>::lowest();
	int left = std::numeric_limits<int>::lowest();
	int top_left = std::numeric_limits<int>::lowest();

	for (int i = 1; i < DPT.size(); i++) {
		for (int j = 1; j < DPT[0].size(); j++) {

			
			top = DPT[i - 1][j] - g;
			left = DPT[i][j - 1] - g;
			top_left = DPT[i - 1][j - 1] + sigma(Q[i-1], T[j-1]);
			DPT[i][j] = max({ top,left,top_left,0 });
			if (DPT[i][j] > best_value) {
				best_value = DPT[i][j];
				best_x = i;
				best_y = j;
			}
		}
	}
	std::cout << "time to completion series: " << std::time(0) - start_time << endl;

	//best x corresponds with the column representing a specific song
	auto js = find_song.find(interval(best_x, best_x));
	if (js != find_song.end()) {
		cout << "song is: " << std::get<0>(js->second) << endl;
	}
	

	//reconstruct path: start at best cell in table and go until top left or get 0 cell (indicating cut off of alignment)
	int x = best_x;
	int y = best_y;
	vector<coord> path;
	path.push_back(coord(x, y));
	while (x > 0 || y > 0) {
		int top = std::numeric_limits<int>::lowest();
		int left = std::numeric_limits<int>::lowest();
		int top_left = std::numeric_limits<int>::lowest();
		if (x == 0) {
			cout << "hi" << endl;
		}
		if (x > 0) {
			top = DPT[x - 1][y];
		}
		if (y > 0) {
			left = DPT[x][y - 1];
		}
		if (x > 0 && y > 0) {
			top_left = DPT[x - 1][y - 1];
		}
		if (top_left < 0 && left < 0 && top < 0) {//reached local cut off
			break;
		}
		if (top > left && top > top_left) {
			path.push_back(coord(x - 1, y));
			x = x - 1;
		}
		else if (left > top && left > top_left) {
			path.push_back(coord(x, y - 1));
			y = y - 1;
		}
		else {
			path.push_back(coord(x - 1, y - 1));
			x = x - 1;
			y = y - 1;
		}
	}
	score = best_value;

	std::cout << "score: " << best_value << endl;

	return path;
}

int smith_waterman_linear(vector<char> Q, vector<char> T, int g, std::function<int(char, char)> sigma, int& score, std::map<interval, json_identifer>find_song) {
	//linear version of smith waterman that doesn't do path reconstruction so it only has to maintain two column of DPT at a time

	vector<vector<short>> rows;
	rows.push_back(vector<short>(T.size(), 0));
	rows.push_back(vector<short>(T.size(), 0));

	int best_value = 0;

	int best_x = 0;
	int best_y = 0;

	bool mod_row = false;

	//!mod_row is previous row, mod_row is current row, alternate to cut down on copy overhead
	for (int i = 0; i < Q.size(); i++) {
		for (int j = 0; j < T.size(); j++) {
			int top = std::numeric_limits<int>::lowest();
			int left = std::numeric_limits<int>::lowest();
			int top_left = std::numeric_limits<int>::lowest();
			if (i > 0) {
				top = rows[!mod_row][j] - g;
			}
			if (j > 0) {
				left = rows[mod_row][j - 1] - g;
			}
			if (i > 0 && j > 0) {
				top_left = rows[!mod_row][j - 1] + sigma(Q[i - 1], T[j - 1]);
			}
			rows[mod_row][j] = max({ top,left,top_left,0 });
			if (rows[mod_row][j] > best_value) {
				best_value = rows[mod_row][j];
				best_x = i;
				best_y = j;
			}
		}
		rows[!mod_row] = vector<short>(T.size(), 0);
		mod_row = !mod_row;
	}

	return best_value;

}

vector<coord> parallel_smith_waterman(vector<char> Q, vector<char> T, int g, std::function<int(char, char)> sigma, int& score) {
	std::vector<std::vector<int>> DPT(Q.size() + 1, std::vector<int>(T.size() + 1, 0));

	//no need for initialization because values should start at 0 in this case

	//need to track largest single cell in table as we go
	int best_x = 0;
	int best_y = 0;
	int best_value = 0;

	int m = Q.size();
	int n = T.size();

	auto start_time = std::time(0);

	for (int k = 0; k <= m + n; ++k) {
		// i runs from k-n to k, clipped to [0..m]
		int i_min = max(0, k - n);
		int i_max = min(k, m);
		#pragma omp parallel for shared(DPT, best_value, best_x, best_y) schedule(dynamic)
		for (int i = i_min; i <= i_max; ++i) {
			int j = k - i;
			// skip the (0,0) base cell if desired, though it stays zero
			if (i == 0 || j == 0) {
				DPT[i][j] = 0;
				continue;
			}
			int top = DPT[i - 1][j] - g;
			int left = DPT[i][j - 1] - g;
			int top_left = DPT[i - 1][j - 1] + sigma(Q[i - 1], T[j - 1]);
			int val = max({ top, left, top_left, 0 });
			DPT[i][j] = val;

			// update global best under a critical section
			#pragma omp critical
			{
				if (val > best_value) {
					best_value = val;
					best_x = i;
					best_y = j;
				}
			}
		}
	}

	std::cout << "time to completion parallel: " << std::time(0) - start_time << endl;

	int x = best_x;
	int y = best_y;
	vector<coord> path;
	path.push_back(coord(x, y));
	while (x > 0 || y > 0) {
		int top = std::numeric_limits<int>::lowest();
		int left = std::numeric_limits<int>::lowest();
		int top_left = std::numeric_limits<int>::lowest();
		if (x > 0) {
			top = DPT[x - 1][j];
		}
		if (y > 0) {
			left = DPT[i][y - 1];
		}
		if (x > 0 && y > 0) {
			top_left = DPT[x - 1][y - 1];
		}
		if (top_left < 0 && left < 0 && top < 0) {//reached local cut off
			break;
		}
		if (top > left && top > top_left) {
			path.push_back(coord(x - 1, y));
			x = x - 1;
		}
		else if (left > top && left > top_left) {
			path.push_back(coord(x, y - 1));
			y = y - 1;
		}
		else {
			path.push_back(coord(x - 1, y - 1));
			x = x - 1;
			y = y - 1;
		}
	}

	score = DPT[Q.size()][T.size()];

	std::cout << "score: " << score << endl;

	return path;
}
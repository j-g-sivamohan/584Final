// 584_final.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include "Directory_Manager.h"
#include "Alignment.h"

using namespace std;

int test_sigma(char a, char b) {
    if (a == -128 || b == -128) {//if border between tracks, make it terrible alignment
        return std::numeric_limits<int>::lowest();
    }
    if (a == b) {
        return 3;
    }
    return -1;
}

int main()
{
    vector<char> values;

    std::map<interval, json_identifer>map_stuff = run_parse(values);

    int score = 0;

    vector<char> test_1 = { 4,3,1,-2 };
    vector<char> test_2 = { 4,3,0,-2 };

    vector<char> Q{};
    vector<char> T{};

    
    for (int i = values.size()-1; i >= 0; i--) {
        if (478 <= i && i < 2021) {
            T.push_back(values[i]);
        }
        else if(5269 <= i && i < 5499) {
            Q.push_back(values[i]);
        }
    }
    

    auto p1 = smith_waterman(Q, T, 5, test_sigma, score, map_stuff);

    //auto path = parallel_smith_waterman(test_1, values, 5, test_sigma, score);

    cout << "score" << endl;

    return 0;
}

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file

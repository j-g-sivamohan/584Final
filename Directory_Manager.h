#pragma once
#include <boost/filesystem.hpp>   
#include "json.h" 
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <tuple>

using namespace std;

namespace fs = boost::filesystem;
using json = nlohmann::json;

using json_identifer = std::tuple<std::string, int, std::string, int, bool>;//key that will go into map with value being the range of the concat string that is 
//corresponding pitch interval

class interval {
public:
    int start;
    int stop;
    interval(int s, int t);
    bool operator<(const interval& other) const;
};

struct TupleHash {
    std::size_t operator()(const json_identifer& t) const {
        std::size_t hash = 0;
        std::hash<std::string> s_hash;
        std::hash<int> i_hash;
        std::hash<bool> b_hash;
        hash += s_hash(std::get<0>(t));
        hash += i_hash(std::get<1>(t));
        hash += s_hash(std::get<2>(t));
        hash += b_hash(std::get<3>(t));
        return hash;
    }
};

using ArtistSongData = std::tuple<std::string, std::string, json>;

std::vector<ArtistSongData> load_all_interval_data(const std::string& base_dir);

std::map<interval, json_identifer> run_parse(vector<char>& interval_values);

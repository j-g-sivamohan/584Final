
#define JSON_HAS_CPP_14 1
#include "Directory_Manager.h"
#include <iostream>
#include <unordered_map>
#include <map>

using namespace std;

interval::interval(int s, int t): start(s), stop(t) {

}
bool interval::operator<(const interval& other) const {
    return other.stop > stop && other.start > start;
}


std::vector<ArtistSongData> load_all_interval_data(string& base_dir) {
    std::vector<ArtistSongData> all_data;

    fs::path basePath(base_dir);
    if (!fs::exists(basePath) || !fs::is_directory(basePath)) {
        std::cerr << "Base directory not found: " << base_dir << "\n";
        return all_data;
    }

    for (fs::directory_iterator artistIt(basePath); artistIt != fs::directory_iterator(); ++artistIt) {
        if (!fs::is_directory(*artistIt)) continue;
        std::string artist = artistIt->path().filename().string();

        for (fs::directory_iterator songIt(artistIt->path()); songIt != fs::directory_iterator(); ++songIt) {
            fs::path songPath = songIt->path();
            if (songPath.extension() != ".json" && songPath.extension() != ".JSON")
                continue;

            std::ifstream inFile(songPath.string());
            if (!inFile) {
                std::cerr << "Failed to open " << songPath << "\n";
                continue;
            }

            try {
                json track_data = json::parse(inFile);
                std::string song_name = songPath.stem().string();
                all_data.emplace_back(artist, song_name, track_data);
            }
            catch (const std::exception& e) {
                std::cerr << "JSON parse error in " << songPath
                    << ": " << e.what() << "\n";
            }
        }
    }

    return all_data;
}

std::map<interval, json_identifer> run_parse(vector<char>& interval_values) {

    std::string base_dir = "D:\clean_midi_deduplicated_and_bytes_intervals_only";

    //test info
    //std::string base_dir = "D:\dummy_folder";
    std::vector<ArtistSongData> all_songs = load_all_interval_data(base_dir);

    std::map<interval, json_identifer> u{};

    interval_values.reserve(39641096 + all_songs.size()+1);

    interval_values.push_back(1);
    cout << interval_values[0] << endl;

    unsigned int current_index = 0;
    unsigned int last_index = 0;

    unsigned int total_size = 0;
    
    for (size_t i = 0; i < all_songs.size(); ++i) {
        std::string artist, song;
        json tracks;
        std::tie(artist, song, tracks) = all_songs[i];  

        for (const auto& track : tracks) {
            
            int idx = track.value("track_index", -1);
            std::string instr = track.value("instrument_name", "Unknown");
            int prog = track.value("program", -1);
            int num_intervals = 0;
            bool isDrum = track.value("is_drum", false);

            //only consider for comparison if criteria are met
            if (track.count("pitch_intervals") && track["pitch_intervals"].is_array()) {

                num_intervals = track["pitch_intervals"].size();
                u.insert(std::make_pair<interval, json_identifer>(interval(last_index, last_index + num_intervals), {song, idx, instr, prog, isDrum}));
                auto &check = track["pitch_intervals"];
                for (auto interval : track["pitch_intervals"]) {
                    interval_values.emplace_back(interval.get<int>());
                }
                interval_values.emplace_back(-128);
                last_index = last_index + num_intervals;
                total_size += num_intervals;
            }
            else {
                continue;
            }
        }
    }
    
    return u;
}

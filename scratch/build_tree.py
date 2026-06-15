import re

with open("src/main.cpp", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject variables at the top (after passScrollIndex)
vars_injection = """int passScrollIndex = 0;

struct TreeItem {
    bool isCategory;
    int categoryIndex; // 0=Tonight, 1=This Week, 2=This Month, 3=Favorites
    int passIndex;     // Index in recommendedPasses
};
bool catExpanded[4] = {false, false, false, false};
std::vector<TreeItem> displayTree;
int selectedPassIndex = -1; // For detail view

void rebuildTree(uint32_t current_unix) {
    displayTree.clear();
    for (int c = 0; c < 4; c++) {
        displayTree.push_back({true, c, -1});
        if (catExpanded[c]) {
            for (int i = 0; i < recommendedPasses.size(); i++) {
                const auto& p = recommendedPasses[i];
                bool match = false;
                if (c == 0 && p.aosTime >= current_unix && p.aosTime < current_unix + 24*3600) match = true;
                else if (c == 1 && p.aosTime >= current_unix && p.aosTime < current_unix + 7*24*3600) match = true;
                else if (c == 2 && p.aosTime >= current_unix && p.aosTime < current_unix + 30*24*3600) match = true;
                else if (c == 3 && p.score >= 4 && p.aosTime >= current_unix) match = true;
                
                if (match) {
                    displayTree.push_back({false, c, i});
                }
            }
        }
    }
}
"""
content = content.replace("int passScrollIndex = 0;", vars_injection)

# 2. Change predictPasses to 30 days
content = content.replace("auto passes = predictor.predictPasses(g_satellites[i].tle, startTime, 7);", "auto passes = predictor.predictPasses(g_satellites[i].tle, startTime, 30);")

# 3. Call rebuildTree when predictions are ready
pred_ready_injection = """        recommendedPasses = upcomingPasses;
        predictionsReady = true;
        rebuildTree(current_unix);"""
content = content.replace("""        recommendedPasses = upcomingPasses;
        predictionsReady = true;""", pred_ready_injection)

# 4. Handle Keyboard input
# Replace the continuous key handler for showRecommendations
# Find:
# } else if (showRecommendations) {
#     if (key == ';') { if (passScrollIndex > 0) passScrollIndex--; }
#     else if (key == '.') { int maxIndex = (int)recommendedPasses.size() - 3; if (maxIndex < 0) maxIndex = 0; if (passScrollIndex < maxIndex) passScrollIndex++; }
# }
old_cont_keys = """                } else if (showRecommendations) {
                    if (key == ';') { if (passScrollIndex > 0) passScrollIndex--; }
                    else if (key == '.') { int maxIndex = (int)recommendedPasses.size() - 3; if (maxIndex < 0) maxIndex = 0; if (passScrollIndex < maxIndex) passScrollIndex++; }
                }"""
new_cont_keys = """                } else if (showRecommendations && selectedPassIndex == -1) {
                    if (key == ';') { if (passScrollIndex > 0) passScrollIndex--; }
                    else if (key == '.') { if (passScrollIndex < (int)displayTree.size() - 1) passScrollIndex++; }
                }"""
content = content.replace(old_cont_keys, new_cont_keys)

# Add Enter/Backspace handling for showRecommendations in the discrete key handler
# We'll inject it into the appState == STATE_MAIN block, before 'w'
old_discrete = """                } else if (M5Cardputer.Keyboard.isKeyPressed('w')) {"""
new_discrete = """                } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_BACKSPACE) || M5Cardputer.Keyboard.isKeyPressed(27) || M5Cardputer.Keyboard.isKeyPressed('`')) {
                    if (showRecommendations) {
                        if (selectedPassIndex != -1) {
                            selectedPassIndex = -1; // Back to tree
                        } else {
                            showRecommendations = false; // Close panel
                        }
                    }
                } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
                    if (appState == STATE_MAIN && !showRecommendations) {
                        showRecommendations = true;
                        rebuildTree(current_unix);
                    } else if (showRecommendations) {
                        if (selectedPassIndex != -1) {
                            selectedPassIndex = -1; // Back to tree
                        } else {
                            // Toggle category or open detail
                            if (passScrollIndex >= 0 && passScrollIndex < displayTree.size()) {
                                auto& item = displayTree[passScrollIndex];
                                if (item.isCategory) {
                                    catExpanded[item.categoryIndex] = !catExpanded[item.categoryIndex];
                                    rebuildTree(current_unix);
                                } else {
                                    selectedPassIndex = item.passIndex;
                                }
                            }
                        }
                    }
                } else if (M5Cardputer.Keyboard.isKeyPressed('w')) {"""
content = content.replace(old_discrete, new_discrete)

# 5. Remove the old "Toggle Pass List" from Enter key in handleContinuousKey/discrete
# Actually, the original Enter was:
# } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
#     showRecommendations = !showRecommendations;
# }
# So let's find that and replace it entirely!
old_discrete_enter = """                } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
                    showRecommendations = !showRecommendations;
                } else if (M5Cardputer.Keyboard.isKeyPressed('w')) {"""
content = content.replace(old_discrete_enter, new_discrete)


# 6. Replace the drawing code for showRecommendations
old_draw = r'// Show top 3 recommendations based on scroll index[\s\S]*?earth_renderer->getCanvas\(\)->drawString\("\[\^/v\]", 105, 5\);\s*\}'
new_draw = """                if (selectedPassIndex != -1) {
                    // Draw Detail View
                    const auto& p = recommendedPasses[selectedPassIndex];
                    earth_renderer->getCanvas()->setTextColor(TFT_CYAN);
                    earth_renderer->getCanvas()->drawString("Name:", 5, 25);
                    earth_renderer->getCanvas()->setTextColor(TFT_WHITE);
                    earth_renderer->getCanvas()->drawString(p.satName.c_str(), 40, 25);
                    
                    earth_renderer->getCanvas()->setTextColor(TFT_CYAN);
                    earth_renderer->getCanvas()->drawString("Orbit:", 5, 37);
                    
                    int tzOffsetSec = pos_manager ? pos_manager->getTimezoneManager()->getTimezoneOffset(baseUserLat, baseUserLon) : 8*3600;
                    time_t aos_t = (time_t)p.aosTime + tzOffsetSec;
                    time_t los_t = (time_t)p.losTime + tzOffsetSec;
                    struct tm * aos_tm = gmtime(&aos_t);
                    struct tm * los_tm = gmtime(&los_t);
                    char timeStr[32];
                    sprintf(timeStr, "%02d:%02d-%02d:%02d", aos_tm->tm_hour, aos_tm->tm_min, los_tm->tm_hour, los_tm->tm_min);
                    earth_renderer->getCanvas()->setTextColor(TFT_LIGHTGRAY);
                    earth_renderer->getCanvas()->drawString(timeStr, 5, 49);
                    
                    earth_renderer->getCanvas()->setTextColor(TFT_CYAN);
                    earth_renderer->getCanvas()->drawString("Peak:", 5, 61);
                    earth_renderer->getCanvas()->setTextColor(TFT_WHITE);
                    earth_renderer->getCanvas()->drawString((String((int)p.maxElevation) + "deg").c_str(), 40, 61);
                    
                    earth_renderer->getCanvas()->setTextColor(TFT_CYAN);
                    earth_renderer->getCanvas()->drawString("Score:", 5, 73);
                    String stars = "";
                    for(int s=0;s<p.score;s++) stars += "*";
                    uint16_t starColor = (p.score==5) ? TFT_GOLD : (p.score>=3 ? TFT_GREEN : TFT_LIGHTGRAY);
                    earth_renderer->getCanvas()->setTextColor(starColor);
                    earth_renderer->getCanvas()->drawString(stars.c_str(), 45, 73);
                    
                    earth_renderer->getCanvas()->setTextColor(TFT_CYAN);
                    earth_renderer->getCanvas()->drawString("Reason:", 5, 85);
                    String reason = "Dark sky";
                    if (p.maxElevation > 60) reason += "+Zenith";
                    if (p.visibleDuration > 300) reason += "+Long";
                    earth_renderer->getCanvas()->setTextColor(TFT_LIGHTGRAY);
                    earth_renderer->getCanvas()->drawString(reason.c_str(), 5, 97);
                    
                } else {
                    // Draw Tree View
                    const char* catNames[] = {"Tonight", "This Week", "This Month", "Favorites"};
                    int y = 20;
                    int itemsPerPage = 8;
                    int startIndex = (passScrollIndex / itemsPerPage) * itemsPerPage;
                    
                    for (int i = 0; i < itemsPerPage && (startIndex + i) < displayTree.size(); i++) {
                        int idx = startIndex + i;
                        const auto& item = displayTree[idx];
                        
                        if (idx == passScrollIndex) {
                            earth_renderer->getCanvas()->fillRect(2, y-1, 136, 11, earth_renderer->getCanvas()->color565(0, 120, 255));
                        }
                        
                        if (item.isCategory) {
                            earth_renderer->getCanvas()->setTextColor(idx == passScrollIndex ? TFT_WHITE : TFT_CYAN);
                            String prefix = catExpanded[item.categoryIndex] ? "[-] " : "[+] ";
                            earth_renderer->getCanvas()->drawString((prefix + catNames[item.categoryIndex]).c_str(), 5, y);
                        } else {
                            const auto& p = recommendedPasses[item.passIndex];
                            earth_renderer->getCanvas()->setTextColor(idx == passScrollIndex ? TFT_WHITE : TFT_LIGHTGRAY);
                            String name = String(p.satName.c_str());
                            if (name.length() > 8) name = name.substring(0, 7) + ".";
                            earth_renderer->getCanvas()->drawString(name.c_str(), 15, y);
                            
                            // Draw stars
                            String stars = "";
                            for(int s=0;s<p.score;s++) stars += "*";
                            uint16_t starColor = (p.score==5) ? TFT_GOLD : (p.score>=3 ? TFT_GREEN : TFT_LIGHTGRAY);
                            if (idx == passScrollIndex) starColor = TFT_WHITE;
                            earth_renderer->getCanvas()->setTextColor(starColor);
                            earth_renderer->getCanvas()->drawString(stars.c_str(), 70, y);
                            
                            // Draw day if not tonight
                            if (item.categoryIndex != 0) {
                                int tzOffsetSec = pos_manager ? pos_manager->getTimezoneManager()->getTimezoneOffset(baseUserLat, baseUserLon) : 8*3600;
                                time_t aos_t = (time_t)p.aosTime + tzOffsetSec;
                                struct tm * aos_tm = gmtime(&aos_t);
                                char dayStr[16];
                                sprintf(dayStr, "%02d/%02d", aos_tm->tm_mon + 1, aos_tm->tm_mday);
                                earth_renderer->getCanvas()->setTextColor(TFT_DARKGREY);
                                earth_renderer->getCanvas()->drawString(dayStr, 105, y);
                            }
                        }
                        y += 11;
                    }
                    
                    if (displayTree.size() > itemsPerPage) {
                        earth_renderer->getCanvas()->setTextColor(TFT_DARKGREY);
                        earth_renderer->getCanvas()->drawString("[^/v]", 110, 5);
                    }
                }"""
content = re.sub(old_draw, new_draw, content)

with open("src/main.cpp", "w", encoding="utf-8") as f:
    f.write(content)

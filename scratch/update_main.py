import re

with open("src/main.cpp", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update AppState Enum
enum_replacement = """enum AppState {
    STATE_MAIN,
    STATE_WIFI_SETUP,
    STATE_SAT_SELECT,
    STATE_REC_MENU,
    STATE_REC_LIST,
    STATE_REC_DETAIL
};"""
content = re.sub(r'enum AppState \{[\s\S]*?\};', enum_replacement, content)

# 2. Update predictorTask
# Find predictorTaskHandle and following variables
vars_replacement = """TaskHandle_t predictorTaskHandle = NULL;
std::vector<PassEvent> allRecommendedPasses;
std::vector<PassEvent> currentRecList;
int recMenuIndex = 0;
int recListIndex = 0;
PassEvent selectedRecPass;
"""
content = re.sub(r'TaskHandle_t predictorTaskHandle = NULL;[\s\S]*?int passScrollIndex = 0;', vars_replacement, content)

# Change predictorTask to predict 30 days
content = content.replace('auto passes = predictor.predictPasses(g_satellites[i].tle, startTime, 7);', 'auto passes = predictor.predictPasses(g_satellites[i].tle, startTime, 30);')

# Change how passes are stored
pass_store_repl = """        portENTER_CRITICAL(&passMutex);
        allRecommendedPasses = upcomingPasses;
        predictionsReady = true;
        portEXIT_CRITICAL(&passMutex);"""
content = content.replace("""        portENTER_CRITICAL(&passMutex);
        recommendedPasses = upcomingPasses;
        predictionsReady = true;
        portEXIT_CRITICAL(&passMutex);""", pass_store_repl)

# 3. Add UI Drawing functions before loop()
# We need to insert drawRecMenu, drawRecList, drawRecDetail
ui_functions = """
void drawRecMenu() {
    auto canvas = earth_renderer->getCanvas();
    uint16_t w = canvas->width();
    uint16_t h = canvas->height();
    canvas->fillRect(0, 0, w, h, canvas->color565(10, 15, 20));
    canvas->fillRect(0, 0, w, 20, canvas->color565(30, 60, 100));
    canvas->setTextColor(TFT_WHITE);
    canvas->setTextSize(1);
    canvas->drawString("RECOMMENDED PASSES", 5, 6);
    
    const char* items[] = {"Tonight (Next 24h)", "This Week (Next 7d)", "This Month (Next 30d)", "Favorites (Score >= 4)"};
    int y = 35;
    for (int i=0; i<4; i++) {
        if (i == recMenuIndex) {
            canvas->fillRect(20, y-2, w-40, 15, canvas->color565(0, 120, 255));
            canvas->setTextColor(TFT_WHITE);
        } else {
            canvas->setTextColor(TFT_LIGHTGRAY);
        }
        canvas->drawString(items[i], 25, y);
        y += 20;
    }
    
    canvas->setTextColor(TFT_DARKGREY);
    canvas->drawString("[^/v] Sel  [Enter] Open  [ESC] Close", 5, h - 12);
}

void drawRecList() {
    auto canvas = earth_renderer->getCanvas();
    uint16_t w = canvas->width();
    uint16_t h = canvas->height();
    canvas->fillRect(0, 0, w, h, canvas->color565(10, 15, 20));
    canvas->fillRect(0, 0, w, 20, canvas->color565(30, 60, 100));
    canvas->setTextColor(TFT_WHITE);
    canvas->setTextSize(1);
    const char* titles[] = {"Tonight", "This Week", "This Month", "Favorites"};
    canvas->drawString(titles[recMenuIndex], 5, 6);
    
    portENTER_CRITICAL(&passMutex);
    if (!predictionsReady) {
        canvas->setTextColor(TFT_YELLOW);
        canvas->drawString("Calculating orbit data...", 10, 40);
        portEXIT_CRITICAL(&passMutex);
        return;
    }
    
    if (currentRecList.empty()) {
        canvas->setTextColor(TFT_LIGHTGRAY);
        canvas->drawString("No passes found for this timeframe.", 10, 40);
    } else {
        int y = 25;
        int itemsPerPage = 4;
        int startIndex = (recListIndex / itemsPerPage) * itemsPerPage;
        
        for (int i = 0; i < itemsPerPage && (startIndex + i) < currentRecList.size(); i++) {
            int idx = startIndex + i;
            if (idx == recListIndex) {
                canvas->fillRect(2, y-2, w-4, 25, canvas->color565(0, 120, 255));
                canvas->setTextColor(TFT_WHITE);
            } else {
                canvas->setTextColor(TFT_LIGHTGRAY);
            }
            
            const auto& p = currentRecList[idx];
            String name = String(p.satName.c_str());
            if(name.length()>12) name = name.substring(0,10)+"..";
            canvas->drawString(name.c_str(), 5, y);
            
            String stars = "";
            for(int s=0;s<p.score;s++) stars += "*";
            uint16_t starColor = (p.score==5) ? TFT_GOLD : (p.score>=3 ? TFT_GREEN : TFT_LIGHTGRAY);
            if (idx == recListIndex) starColor = TFT_WHITE;
            canvas->setTextColor(starColor);
            canvas->drawString(stars.c_str(), 80, y);
            
            // Time
            int tzOffsetSec = pos_manager ? pos_manager->getTimezoneManager()->getTimezoneOffset(baseUserLat, baseUserLon) : 8*3600;
            time_t aos_t = (time_t)p.aosTime + tzOffsetSec;
            struct tm * aos_tm = gmtime(&aos_t);
            char timeStr[32];
            sprintf(timeStr, "%02d/%02d %02d:%02d", aos_tm->tm_mon + 1, aos_tm->tm_mday, aos_tm->tm_hour, aos_tm->tm_min);
            if (idx != recListIndex) canvas->setTextColor(TFT_LIGHTGRAY);
            canvas->drawString(timeStr, w - 75, y);
            
            y += 24;
        }
    }
    portEXIT_CRITICAL(&passMutex);
    
    canvas->setTextColor(TFT_DARKGREY);
    canvas->drawString("[^/v] Sel  [Enter] Detail  [ESC] Back", 5, h - 12);
}

void drawRecDetail() {
    auto canvas = earth_renderer->getCanvas();
    uint16_t w = canvas->width();
    uint16_t h = canvas->height();
    canvas->fillRect(0, 0, w, h, canvas->color565(15, 25, 35));
    
    const auto& p = selectedRecPass;
    canvas->fillRect(0, 0, w, 22, canvas->color565(100, 50, 200));
    canvas->setTextColor(TFT_WHITE);
    canvas->setTextSize(1);
    canvas->drawString(("Details: " + String(p.satName.c_str())).c_str(), 5, 7);
    
    int tzOffsetSec = pos_manager ? pos_manager->getTimezoneManager()->getTimezoneOffset(baseUserLat, baseUserLon) : 8*3600;
    time_t aos_t = (time_t)p.aosTime + tzOffsetSec;
    time_t los_t = (time_t)p.losTime + tzOffsetSec;
    struct tm * aos_tm = gmtime(&aos_t);
    struct tm * los_tm = gmtime(&los_t);
    
    char aosStr[32], losStr[32];
    sprintf(aosStr, "%02d:%02d:%02d", aos_tm->tm_hour, aos_tm->tm_min, aos_tm->tm_sec);
    sprintf(losStr, "%02d:%02d:%02d", los_tm->tm_hour, los_tm->tm_min, los_tm->tm_sec);
    
    auto getAzStr = [](float az) -> const char* {
        const char* dirs[] = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
        int idx = (int)round(az / 45.0) % 8;
        if (idx < 0) idx += 8;
        return dirs[idx];
    };
    
    canvas->setTextColor(TFT_CYAN);
    canvas->drawString("Orbit:", 5, 30);
    canvas->setTextColor(TFT_WHITE);
    canvas->drawString((String(aosStr) + " (" + getAzStr(p.startAz) + ") -> " + String(losStr) + " (" + getAzStr(p.endAz) + ")").c_str(), 45, 30);
    
    canvas->setTextColor(TFT_CYAN);
    canvas->drawString("Peak:", 5, 45);
    canvas->setTextColor(TFT_WHITE);
    canvas->drawString((String((int)p.maxElevation) + " deg, Azimuth: " + getAzStr(p.maxAz)).c_str(), 45, 45);
    
    canvas->setTextColor(TFT_CYAN);
    canvas->drawString("Score:", 5, 60);
    String stars = "";
    for(int s=0;s<p.score;s++) stars += "*";
    uint16_t starColor = (p.score==5) ? TFT_GOLD : (p.score>=3 ? TFT_GREEN : TFT_LIGHTGRAY);
    canvas->setTextColor(starColor);
    canvas->drawString(stars.c_str(), 45, 60);
    
    canvas->setTextColor(TFT_CYAN);
    canvas->drawString("Reason:", 5, 75);
    canvas->setTextColor(TFT_LIGHTGRAY);
    String reason = "Dark sky + Satellite illuminated";
    if (p.maxElevation > 60) reason += ", Zenith pass";
    if (p.visibleDuration > 300) reason += ", Long duration";
    drawWrappedText(canvas, reason, 55, 75, w - 60, 10);
    
    canvas->setTextColor(TFT_DARKGREY);
    canvas->drawString("[ESC] Back to List", 5, h - 12);
}

void loop() {"""

content = content.replace("void loop() {", ui_functions)

# 4. Keyboard handlers inside loop()
kb_handlers = """
        if (M5Cardputer.Keyboard.isChange() && M5Cardputer.Keyboard.isPressed()) {
            if (appState == STATE_MAIN) {
                if (M5Cardputer.Keyboard.isKeyPressed('c')) {
                    isManualLocationMode = !isManualLocationMode;
                    if (!isManualLocationMode) {
                        triggerPrediction = true;
                        portENTER_CRITICAL(&passMutex);
                        predictionsReady = false;
                        portEXIT_CRITICAL(&passMutex);
                    }
                } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
                    appState = STATE_REC_MENU;
                } else if (M5Cardputer.Keyboard.isKeyPressed('w')) {
"""
content = re.sub(
    r'if \(M5Cardputer\.Keyboard\.isChange\(\) && M5Cardputer\.Keyboard\.isPressed\(\)\) \{\s*if \(appState == STATE_MAIN\) \{\s*if \(M5Cardputer\.Keyboard\.isKeyPressed\(\'c\'\)\) \{[\s\S]*?\} else if \(M5Cardputer\.Keyboard\.isKeyPressed\(KEY_ENTER\)\) \{[\s\S]*?\} else if \(M5Cardputer\.Keyboard\.isKeyPressed\(\'w\'\)\) \{',
    kb_handlers,
    content
)

kb_handlers_extended = """                    } else if (M5Cardputer.Keyboard.isKeyPressed('.') || M5Cardputer.Keyboard.isKeyPressed(';')) { // UP/DOWN Handled in continuous block for MAIN
                        // Do nothing for discrete up/down in MAIN to avoid double trigger
                    }
                }
            } else if (appState == STATE_REC_MENU) {
                if (M5Cardputer.Keyboard.isKeyPressed(KEY_BACKSPACE) || M5Cardputer.Keyboard.isKeyPressed(27) || M5Cardputer.Keyboard.isKeyPressed('`')) {
                    appState = STATE_MAIN;
                } else if (M5Cardputer.Keyboard.isKeyPressed(';')) {
                    if (recMenuIndex > 0) recMenuIndex--;
                } else if (M5Cardputer.Keyboard.isKeyPressed('.')) {
                    if (recMenuIndex < 3) recMenuIndex++;
                } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
                    // Populate currentRecList
                    portENTER_CRITICAL(&passMutex);
                    currentRecList.clear();
                    uint32_t now = current_unix;
                    for (const auto& p : allRecommendedPasses) {
                        if (recMenuIndex == 0) { // Tonight (24h)
                            if (p.aosTime >= now && p.aosTime < now + 24*3600) currentRecList.push_back(p);
                        } else if (recMenuIndex == 1) { // This Week (7d)
                            if (p.aosTime >= now && p.aosTime < now + 7*24*3600) currentRecList.push_back(p);
                        } else if (recMenuIndex == 2) { // This Month (30d)
                            if (p.aosTime >= now && p.aosTime < now + 30*24*3600) currentRecList.push_back(p);
                        } else if (recMenuIndex == 3) { // Favorites
                            if (p.score >= 4 && p.aosTime >= now) currentRecList.push_back(p);
                        }
                    }
                    portEXIT_CRITICAL(&passMutex);
                    recListIndex = 0;
                    appState = STATE_REC_LIST;
                }
            } else if (appState == STATE_REC_LIST) {
                if (M5Cardputer.Keyboard.isKeyPressed(KEY_BACKSPACE) || M5Cardputer.Keyboard.isKeyPressed(27) || M5Cardputer.Keyboard.isKeyPressed('`')) {
                    appState = STATE_REC_MENU;
                } else if (M5Cardputer.Keyboard.isKeyPressed(';')) {
                    if (recListIndex > 0) recListIndex--;
                } else if (M5Cardputer.Keyboard.isKeyPressed('.')) {
                    if (recListIndex < (int)currentRecList.size() - 1) recListIndex++;
                } else if (M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
                    if (!currentRecList.empty()) {
                        selectedRecPass = currentRecList[recListIndex];
                        appState = STATE_REC_DETAIL;
                    }
                }
            } else if (appState == STATE_REC_DETAIL) {
                if (M5Cardputer.Keyboard.isKeyPressed(KEY_BACKSPACE) || M5Cardputer.Keyboard.isKeyPressed(27) || M5Cardputer.Keyboard.isKeyPressed('`') || M5Cardputer.Keyboard.isKeyPressed(KEY_ENTER)) {
                    appState = STATE_REC_LIST;
                }
            } else if (appState == STATE_SAT_SELECT) {"""
content = content.replace("            } else if (appState == STATE_SAT_SELECT) {", kb_handlers_extended)


# Remove the continuous key handling for recommendations since we moved it
content = re.sub(
    r'\} else if \(showRecommendations\) \{[\s\S]*?\}',
    '}',
    content
)

# Remove the old drawing code for showRecommendations
content = re.sub(
    r'        if \(showRecommendations\) \{[\s\S]*?\} else if \(appState == STATE_MAIN\) \{',
    '        if (appState == STATE_MAIN) {',
    content
)

# Fix draw coordinate overlay logic
content = content.replace('if (!showRecommendations && !showHelp && appState == STATE_MAIN)', 'if (!showHelp && appState == STATE_MAIN)')


# Add the drawing calls for the new states
render_states = """        if (appState == STATE_WIFI_SETUP) {
            drawWiFiSetupPage();
            earth_renderer->getCanvas()->pushSprite(0, 0);
            
            if (wifiIsScanning) {
                wifiNetworks = HalWifi::scanNetworks();
                wifiIsScanning = false;
                wifiSelectedIndex = 0;
            }
            return;
        } else if (appState == STATE_SAT_SELECT) {
            drawSatSelectPage();
            earth_renderer->getCanvas()->pushSprite(0, 0);
            return;
        } else if (appState == STATE_REC_MENU) {
            drawRecMenu();
            earth_renderer->getCanvas()->pushSprite(0, 0);
            return;
        } else if (appState == STATE_REC_LIST) {
            drawRecList();
            earth_renderer->getCanvas()->pushSprite(0, 0);
            return;
        } else if (appState == STATE_REC_DETAIL) {
            drawRecDetail();
            earth_renderer->getCanvas()->pushSprite(0, 0);
            return;
        }"""
content = re.sub(r'        if \(appState == STATE_WIFI_SETUP\) \{[\s\S]*?return;\n        \}', render_states, content)

with open("src/main.cpp", "w", encoding="utf-8") as f:
    f.write(content)

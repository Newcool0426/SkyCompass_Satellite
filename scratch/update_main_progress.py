import re

with open("src/main.cpp", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add progress variable
if "int predictionProgress =" not in content:
    content = content.replace("bool predictionsReady = false;", "bool predictionsReady = false;\nint predictionProgress = 0;")

# 2. Update predictorTask to update progress and predict 7 days
old_task = """        for (int i = 0; i < NUM_SATELLITES; i++) {
            if (triggerPrediction) break;
            
            if (g_satellites[i].selected) {
                auto passes = predictor.predictPasses(g_satellites[i].tle, startTime, 30);
                allPasses.insert(allPasses.end(), passes.begin(), passes.end());
                vTaskDelay(pdMS_TO_TICKS(10)); // Yield between satellites
            }
        }"""
new_task = """        predictionProgress = 0;
        for (int i = 0; i < NUM_SATELLITES; i++) {
            if (triggerPrediction) break;
            
            if (g_satellites[i].selected) {
                auto passes = predictor.predictPasses(g_satellites[i].tle, startTime, 7);
                allPasses.insert(allPasses.end(), passes.begin(), passes.end());
                vTaskDelay(pdMS_TO_TICKS(10)); // Yield between satellites
            }
            predictionProgress = i + 1;
        }"""
content = content.replace(old_task, new_task)

# 3. Update drawing code to show progress
old_draw = """            if (!predictionsReady) {
                earth_renderer->getCanvas()->setTextColor(TFT_YELLOW);
                earth_renderer->getCanvas()->drawString("Calculating...", 5, 30);
            } else {"""
new_draw = """            if (!predictionsReady) {
                earth_renderer->getCanvas()->setTextColor(TFT_YELLOW);
                char buf[32];
                sprintf(buf, "Calculating... %d/%d", predictionProgress, NUM_SATELLITES);
                earth_renderer->getCanvas()->drawString(buf, 5, 30);
            } else {"""
content = content.replace(old_draw, new_draw)

# 4. Remove 30 days logic in rebuildTree (change back to 7 days)
content = content.replace("else if (c == 2 && p.aosTime >= current_unix && p.aosTime < current_unix + 30*24*3600) match = true;", "else if (c == 2 && p.aosTime >= current_unix && p.aosTime < current_unix + 7*24*3600) match = true;")
# Also update the category name "This Month" to "Next 7 Days"
content = content.replace('const char* catNames[] = {"Tonight", "This Week", "This Month", "Favorites"};', 'const char* catNames[] = {"Tonight", "This Week", "Next 7 Days", "Favorites"};')

with open("src/main.cpp", "w", encoding="utf-8") as f:
    f.write(content)

#include <Arduino.h>
#include <Sgp4.h>
#include <Ticker.h>

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Sgp4 sgp4;
    // ISS TLE
    sgp4.site(-15.0, -113.0, 0);
    sgp4.init("ISS", "1 25544U 98067A   24166.12345678  .00012345  00000-0  12345-3 0  9999", "2 25544  51.6400 123.4567 0001234 123.4567 123.4567 15.50000000123456");
    
    uint32_t start = millis();
    int iters = 1000;
    for (int i=0; i<iters; i++) {
        sgp4.findPosition(2460461.5 + (i * 0.001));
    }
    uint32_t end = millis();
    
    Serial.printf("1000 iters took %d ms\n", (end - start));
    Serial.printf("Per iter: %.3f ms\n", (float)(end - start) / iters);
}

void loop() {}

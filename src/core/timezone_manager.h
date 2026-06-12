#ifndef TIMEZONE_MANAGER_H
#define TIMEZONE_MANAGER_H

#include <Arduino.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>

/**
 * @brief 时区管理器
 * 负责融合在线IP定位与离线网格地图，提供全球高精度时区推算
 */
class TimezoneManager {
private:
    int _currentOffset;         // 当前时区偏移量（秒），例如 UTC+8 为 28800
    bool _isOnlineOffsetValid;  // 在线获取的时区是否有效
    Preferences _preferences;   // NVS 存储
    
    // 从离线网格地图获取时区偏移
    int getOfflineOffset(float latitude, float longitude);
    
    // 从在线 API 获取时区偏移
    bool fetchOnlineOffset();

public:
    TimezoneManager();
    ~TimezoneManager();

    /**
     * @brief 初始化时区管理器（从NVS加载上次保存的时区）
     */
    void begin();

    /**
     * @brief 更新网络时区（需要WiFi已连接）
     * @return 是否成功获取并在本地更新
     */
    bool updateOnlineTimezone();

    /**
     * @brief 获取当前最佳时区偏移量（秒）
     * @param latitude 当前纬度（如果没有GNSS传0.0）
     * @param longitude 当前经度（如果没有GNSS传0.0）
     * @return 时区偏移量（秒）
     */
    int getTimezoneOffset(float latitude, float longitude);
    
    /**
     * @brief 强制设置时区偏移量（秒）并保存
     * @param offsetSeconds 偏移量（秒）
     */
    void setTimezoneOffset(int offsetSeconds);
};

#endif // TIMEZONE_MANAGER_H

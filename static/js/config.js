/**
 * 前端配置管理模組
 * 統一管理所有 HTML 頁面的 API 配置
 */

// 全域配置物件
window.AppConfig = {
    // API 基礎 URL - 將從後端動態載入
    API_BASE: null,
    
    // 其他配置
    APP_NAME: '災民補助申請系統',
    DEBUG: false,
    
    // 初始化標記
    isInitialized: false
};

/**
 * 初始化配置 - 從後端 API 載入配置
 */
async function initializeConfig() {
    if (window.AppConfig.isInitialized) {
        return window.AppConfig;
    }
    
    try {
        // 🔧 修復：直接使用當前頁面的 origin 作為 API base
        // 這樣可以避免 CORS 問題，因為前端和後端使用同一個網址
        const apiBase = window.location.origin + '/api/v1';
        
        console.log('🌐 使用當前網址作為 API Base:', apiBase);
        
        // 更新全域配置
        window.AppConfig.API_BASE = apiBase;
        window.AppConfig.APP_NAME = '災民補助申請系統';
        window.AppConfig.DEBUG = false;
        window.AppConfig.isInitialized = true;
        
        console.log('✅ 配置已載入:', window.AppConfig);
        
        // 可選：仍然從後端獲取其他配置（不會影響 API_BASE）
        try {
            const response = await fetch('/api/v1/config/frontend');
            if (response.ok) {
                const config = await response.json();
                window.AppConfig.APP_NAME = config.app_name || window.AppConfig.APP_NAME;
                window.AppConfig.DEBUG = config.debug || window.AppConfig.DEBUG;
            }
        } catch (e) {
            console.log('ℹ️ 無法載入額外配置（使用預設值）');
        }
        
    } catch (error) {
        console.error('❌ 載入配置失敗:', error);
        // 失敗時使用預設配置
        window.AppConfig.API_BASE = window.location.origin + '/api/v1';
        window.AppConfig.isInitialized = true;
    }
    
    return window.AppConfig;
}

/**
 * 獲取 API 基礎 URL
 */
function getApiBase() {
    if (!window.AppConfig.isInitialized) {
        console.warn('配置尚未初始化，請先呼叫 initializeConfig()');
        return '/api/v1'; // 預設值
    }
    return window.AppConfig.API_BASE;
}

/**
 * 便捷函數：確保配置已初始化後執行回調
 */
async function withConfig(callback) {
    await initializeConfig();
    return callback(window.AppConfig);
}

// 當頁面載入完成時自動初始化配置
document.addEventListener('DOMContentLoaded', function() {
    initializeConfig();
});

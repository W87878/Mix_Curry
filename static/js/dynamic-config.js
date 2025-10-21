/**
 * 簡化版配置管理 - 直接注入到現有 HTML
 * 避免修改現有變數宣告
 */

// 動態設定 API_BASE
(async function() {
    try {
        // 從後端獲取配置
        const response = await fetch('/api/v1/config/frontend');
        
        if (response.ok) {
            const config = await response.json();
            
            // 如果全域變數 API_BASE 存在，就更新它
            if (typeof window.API_BASE !== 'undefined') {
                window.API_BASE = config.api_base_url;
            }
            
            // 也設定為全域變數供其他腳本使用
            window.AppConfig = {
                API_BASE: config.api_base_url,
                APP_NAME: config.app_name,
                DEBUG: config.debug
            };
            
            console.log('動態配置已載入:', window.AppConfig);
            
            // 觸發自定義事件，通知其他腳本配置已載入
            window.dispatchEvent(new CustomEvent('configLoaded', { 
                detail: window.AppConfig 
            }));
        } else {
            console.warn('無法載入後端配置，使用預設值');
            // 使用當前 ngrok URL 作為預設值
            const defaultApiBase = window.location.origin.includes('ngrok') 
                ? window.location.origin + '/api/v1'
                : '/api/v1';
                
            window.AppConfig = {
                API_BASE: defaultApiBase,
                APP_NAME: '災民補助申請系統',
                DEBUG: false
            };
            
            // 同步更新全域變數
            if (typeof window.API_BASE !== 'undefined') {
                window.API_BASE = defaultApiBase;
            }
            
            window.dispatchEvent(new CustomEvent('configLoaded', { 
                detail: window.AppConfig 
            }));
        }
    } catch (error) {
        console.error('載入配置失敗:', error);
        // 使用當前域名構建預設配置
        const defaultApiBase = window.location.origin.includes('ngrok') 
            ? window.location.origin + '/api/v1'
            : '/api/v1';
            
        window.AppConfig = {
            API_BASE: defaultApiBase,
            APP_NAME: '災民補助申請系統',
            DEBUG: false
        };
        
        // 同步更新全域變數
        if (typeof window.API_BASE !== 'undefined') {
            window.API_BASE = defaultApiBase;
        }
        
        window.dispatchEvent(new CustomEvent('configLoaded', { 
            detail: window.AppConfig 
        }));
    }
})();

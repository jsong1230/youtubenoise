/**
 * 대시보드 JavaScript
 * 실시간 통계 업데이트 (30초마다)
 */

// API 엔드포인트
const API_BASE = '/api';

/**
 * 채널 통계 업데이트
 */
async function updateChannelStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) {
            throw new Error('통계 데이터를 가져올 수 없습니다.');
        }
        const data = await response.json();
        
        // 통계 카드 업데이트
        updateStatCard('total_videos', data.total_videos || 0);
        updateStatCard('total_views', formatNumber(data.total_views || 0));
        updateStatCard('total_subscribers', formatNumber(data.total_subscribers || 0));
        updateStatCard('total_watch_time_hours', `${(data.total_watch_time_hours || 0).toFixed(1)}시간`);
        
    } catch (error) {
        console.error('통계 업데이트 실패:', error);
    }
}

/**
 * API 사용량 업데이트
 */
async function updateAPIUsage() {
    try {
        const response = await fetch(`${API_BASE}/usage`);
        if (!response.ok) {
            throw new Error('API 사용량 데이터를 가져올 수 없습니다.');
        }
        const data = await response.json();
        
        // API 사용량 표시 (향후 구현)
        console.log('API 사용량:', data);
        
    } catch (error) {
        console.error('API 사용량 업데이트 실패:', error);
    }
}

/**
 * 통계 카드 업데이트 헬퍼 함수
 */
function updateStatCard(selector, value) {
    // 실제 구현은 DOM 구조에 따라 달라질 수 있음
    // 현재는 기본 구조만 제공
}

/**
 * 숫자 포맷팅 (천 단위 콤마)
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * 초기화 및 주기적 업데이트
 */
document.addEventListener('DOMContentLoaded', function() {
    // 초기 로드
    updateChannelStats();
    updateAPIUsage();
    
    // 30초마다 업데이트
    setInterval(() => {
        updateChannelStats();
        updateAPIUsage();
    }, 30000);
});


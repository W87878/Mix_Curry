// 新版 Admin 後台功能
// 過濾和搜尋功能
let allApplications = [];
let currentView = 'list'; // 'list' or 'map'
let applicationsMapInstance = null;
let mapMarkers = [];

async function loadPendingApplications() {
  try {
    // 改為載入所有案件，而不只是 pending
    const result = await fetch(`${API_BASE}/applications/?limit=1000`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (result.ok) {
      const response = await result.json();
      
      let apps = [];
      if (Array.isArray(response)) {
        apps = response;
      } else if (response.data) {
        if (response.data.applications && Array.isArray(response.data.applications)) {
          apps = response.data.applications;
        } else if (Array.isArray(response.data)) {
          apps = response.data;
        } else {
          apps = [response.data];
        }
      } else if (response.applications) {
        apps = Array.isArray(response.applications) ? response.applications : [response.applications];
      }

      console.log('載入案件數量:', apps.length, apps);
      
      allApplications = apps;
      
      // 更新統計卡片
      updateStatCards(apps);
      
      // 顯示案件列表
      displayApplicationsList(apps);
    } else {
      console.error('載入案件失敗:', result.status);
      allApplications = [];
      updateStatCards([]);
      displayApplicationsList([]);
    }
  } catch (error) {
    console.error('載入案件錯誤:', error);
    allApplications = [];
    updateStatCards([]);
    displayApplicationsList([]);
  }
}

// 更新統計卡片
function updateStatCards(apps) {
  const pending = apps.filter(app => app.status === 'pending').length;
  const inspection = apps.filter(app => app.status === 'site_inspection' || app.status === 'under_review').length;
  const rejected = apps.filter(app => app.status === 'rejected').length;
  const approved = apps.filter(app => app.status === 'approved' || app.status === 'completed').length;
  
  document.getElementById('statPending').textContent = pending || '0';
  document.getElementById('statInspection').textContent = inspection || '0';
  document.getElementById('statRejected').textContent = rejected || '0';
  document.getElementById('statCompleted').textContent = approved || '0';
  
  console.log('統計更新:', { pending, inspection, rejected, approved, total: apps.length });
}

// 切換檢視模式
function switchView(view) {
  currentView = view;
  
  // 更新 tab 樣式
  document.getElementById('listViewTab').classList.toggle('active', view === 'list');
  document.getElementById('mapViewTab').classList.toggle('active', view === 'map');
  
  // 切換顯示
  document.getElementById('listView').style.display = view === 'list' ? 'block' : 'none';
  document.getElementById('mapView').style.display = view === 'map' ? 'block' : 'none';
  
  if (view === 'map') {
    initializeApplicationsMap();
  }
}

// 初始化地圖
function initializeApplicationsMap() {
  if (!applicationsMapInstance) {
    const mapDiv = document.getElementById('applicationsMap');
    applicationsMapInstance = new google.maps.Map(mapDiv, {
      center: { lat: 23.5, lng: 121 },
      zoom: 8,
      mapTypeControl: true,
      streetViewControl: false,
      fullscreenControl: true,
    });
  }
  
  // 根據當前篩選顯示標記
  updateMapMarkers();
}

// 更新地圖標記
function updateMapMarkers() {
  // 清除舊標記
  mapMarkers.forEach(marker => marker.setMap(null));
  mapMarkers = [];
  
  if (!applicationsMapInstance) return;
  
  // 獲取當前篩選的案件
  const filteredApps = getFilteredApplications();
  const bounds = new google.maps.LatLngBounds();
  let markersAdded = 0;
  
  filteredApps.forEach(app => {
    const location = app.damage_location || app.address;
    if (!location) return;
    
    // 使用 Geocoding API
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: location }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const position = results[0].geometry.location;
        
        const marker = new google.maps.Marker({
          position: position,
          map: applicationsMapInstance,
          title: `${app.case_no} - ${app.applicant_name}`,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: getStatusColor(app.status),
            fillOpacity: 0.9,
            strokeColor: '#fff',
            strokeWeight: 2,
          }
        });
        
        // 點擊標記顯示資訊
        marker.addListener('click', () => {
          const infoWindow = new google.maps.InfoWindow({
            content: `
              <div style="padding: 8px;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px;">${app.case_no}</h4>
                <p style="margin: 4px 0; font-size: 13px;"><strong>申請人：</strong>${app.applicant_name}</p>
                <p style="margin: 4px 0; font-size: 13px;"><strong>災害類型：</strong>${getDisasterTypeText(app.disaster_type)}</p>
                <p style="margin: 4px 0; font-size: 13px;"><strong>地址：</strong>${location}</p>
                <button onclick="openReviewModal(${JSON.stringify(app).replace(/"/g, '&quot;')})" 
                  style="margin-top: 8px; padding: 6px 12px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;">
                  前往審核
                </button>
              </div>
            `
          });
          infoWindow.open(applicationsMapInstance, marker);
        });
        
        mapMarkers.push(marker);
        bounds.extend(position);
        markersAdded++;
        
        // 調整地圖視野
        if (markersAdded > 0) {
          applicationsMapInstance.fitBounds(bounds);
        }
      }
    });
  });
}

function getStatusColor(status) {
  const colors = {
    'pending': '#dc2626',
    'under_review': '#d97706',
    'site_inspection': '#d97706',
    'approved': '#059669',
    'completed': '#059669',
    'rejected': '#ea580c'
  };
  return colors[status] || '#999';
}

// 獲取篩選後的案件
function getFilteredApplications() {
  const filterCity = document.getElementById('filterCity')?.value || '';
  const filterTownship = document.getElementById('filterTownship')?.value || '';
  const filterVillage = document.getElementById('filterVillage')?.value || '';
  const filterDisasterType = document.getElementById('filterDisasterType')?.value || '';
  const filterStatus = document.getElementById('filterStatus')?.value || '';
  const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';

  let filtered = allApplications;

  // 按地區過濾
  if (filterCity) {
    filtered = filtered.filter(app => 
      (app.address && app.address.includes(filterCity)) ||
      (app.damage_location && app.damage_location.includes(filterCity))
    );
  }
  
  if (filterTownship) {
    filtered = filtered.filter(app => 
      (app.address && app.address.includes(filterTownship)) ||
      (app.damage_location && app.damage_location.includes(filterTownship))
    );
  }
  
  if (filterVillage) {
    filtered = filtered.filter(app => 
      (app.address && app.address.includes(filterVillage)) ||
      (app.damage_location && app.damage_location.includes(filterVillage))
    );
  }

  // 按災害類型過濾
  if (filterDisasterType) {
    filtered = filtered.filter(app => app.disaster_type === filterDisasterType);
  }

  // 按狀態過濾
  if (filterStatus) {
    filtered = filtered.filter(app => app.status === filterStatus);
  }

  // 按搜尋詞過濾
  if (searchTerm) {
    filtered = filtered.filter(app => 
      (app.case_no && app.case_no.toLowerCase().includes(searchTerm)) ||
      (app.applicant_name && app.applicant_name.toLowerCase().includes(searchTerm)) ||
      (app.address && app.address.toLowerCase().includes(searchTerm)) ||
      (app.damage_location && app.damage_location.toLowerCase().includes(searchTerm)) ||
      (app.phone && app.phone.includes(searchTerm))
    );
  }

  return filtered;
}

function filterApplications() {
  const filtered = getFilteredApplications();
  
  if (currentView === 'list') {
    displayApplicationsList(filtered);
  } else {
    updateMapMarkers();
  }
}

// 按狀態篩選
function filterByStatus(status) {
  document.getElementById('filterStatus').value = status;
  filterApplications();
  
  // 更新統計卡片激活狀態
  document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
  event.target.closest('.stat-card').classList.add('active');
}

// 顯示案件列表（新版：一排一個）
function displayApplicationsList(apps) {
  const container = document.getElementById('applicationsList');

  if (!apps || apps.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 60px 20px; color: #999;">
        <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
        <p style="font-size: 16px; font-weight: 500;">目前沒有符合條件的案件</p>
      </div>
    `;
    return;
  }

  const html = apps.map(app => `
    <div class="application-row">
      <div class="row-left">
        <span class="row-status-badge ${app.status}">${getStatusText(app.status)}</span>
        <div class="row-info">
          <div class="row-applicant">
            <div class="applicant-name">${app.applicant_name || '未提供'}</div>
            <div class="case-number">${app.case_no || 'N/A'}</div>
          </div>
          <div class="row-disaster">${getDisasterTypeText(app.disaster_type)}</div>
          <div class="row-location">📍 ${app.damage_location || app.address || '未提供地址'}</div>
          <div class="row-date">${new Date(app.submitted_at || app.created_at).toLocaleDateString('zh-TW')}</div>
        </div>
      </div>
      <div class="row-actions">
        <button class="btn-navigate" onclick="showLocationOnMapModal('${app.id}', '${(app.damage_location || app.address || '').replace(/'/g, "\\'")}')">
          導航
        </button>
        <button class="btn-review" onclick='openReviewModal(${JSON.stringify(app).replace(/'/g, "\\'")})'> 
          前往審核
        </button>
      </div>
    </div>
  `).join('');

  container.innerHTML = html;
}

// 在 Modal 中顯示位置
function showLocationOnMapModal(appId, location) {
  if (!location || location === '未提供地址') {
    alert('此案件未提供地址資訊');
    return;
  }
  
  // 直接在 Google Maps 中開啟
  const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(location)}`;
  window.open(url, '_blank');
}

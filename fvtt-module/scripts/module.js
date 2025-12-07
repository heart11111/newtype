/**
 * Newtype - RP Analysis Engine
 * 실시간 채팅 분석 및 분위기 감지
 */

const MODULE_ID = 'newtype';
const API_SERVER = 'http://140.245.68.52:8000';

// ============================================================================
// State
// ============================================================================

let engineRunning = false;
let messageBuffer = [];
let lastAnalysis = 0;

// 설정값
const CONFIG = {
  ANALYSIS_INTERVAL: 3 * 60 * 1000,  // 3분
  BUFFER_SIZE: 15,                    // 최대 15개 메시지
  MIN_MESSAGES: 5,                    // 최소 5개
  MIN_MESSAGE_LENGTH: 30,             // 최소 30자
  HIGHLIGHT_THRESHOLD: 70             // 하이라이트 임계값
};

// 현재 분위기 상태
let currentAtmosphere = {
  mood: 'neutral',
  intensity: 0,
  is_highlight: false,
  scene_summary: '',
  timestamp: 0
};

// ============================================================================
// Initialize
// ============================================================================

Hooks.once('init', () => {
  console.log(`${MODULE_ID} | Initializing Newtype Engine`);

  // 전역 API 노출
  game.newtype = {
    // 상태 조회
    isRunning: () => engineRunning,
    getAtmosphere: () => currentAtmosphere,
    getBuffer: () => [...messageBuffer],

    // 제어
    start: () => startEngine(),
    stop: () => stopEngine(),

    // 수동 분석
    analyze: () => analyzeAtmosphere(),

    // 이벤트 리스너 등록 (다른 모듈에서 사용)
    onAtmosphereChange: null,  // callback 등록 가능
    onHighlight: null          // callback 등록 가능
  };
});

Hooks.once('ready', () => {
  console.log(`${MODULE_ID} | Newtype Engine ready`);
});

// ============================================================================
// Chat Message Hook
// ============================================================================

Hooks.on('createChatMessage', async (message, options, userId) => {
  if (!engineRunning) return;

  const content = message.content || '';

  // OOC 메시지 제외
  if (isOOC(content)) return;

  // 짧은 메시지 제외
  if (content.length < CONFIG.MIN_MESSAGE_LENGTH) return;

  // 버퍼에 추가
  messageBuffer.push({
    speaker: message.speaker?.alias || 'Unknown',
    content: content,
    timestamp: Date.now(),
    actorId: message.speaker?.actor || null
  });

  console.log(`[Newtype] Message buffered: ${messageBuffer.length}`);

  // 버퍼 크기 제한
  if (messageBuffer.length > CONFIG.BUFFER_SIZE) {
    messageBuffer.shift();
  }

  // 분석 조건 체크
  const shouldAnalyze =
    messageBuffer.length >= CONFIG.MIN_MESSAGES &&
    (Date.now() - lastAnalysis) >= CONFIG.ANALYSIS_INTERVAL;

  if (shouldAnalyze) {
    await analyzeAtmosphere();
  }
});

// ============================================================================
// Core Functions
// ============================================================================

function isOOC(content) {
  // OOC 패턴 감지
  const oocPatterns = [
    /^\s*\(/,           // (로 시작
    /^\s*\/\//,         // //로 시작
    /^\s*ooc/i,         // ooc로 시작
    /^\s*\[ooc\]/i,     // [ooc]로 시작
    /^\s*<ooc>/i        // <ooc>로 시작
  ];

  return oocPatterns.some(pattern => pattern.test(content));
}

async function analyzeAtmosphere() {
  if (messageBuffer.length < CONFIG.MIN_MESSAGES) return;

  console.log(`[Newtype] Analyzing ${messageBuffer.length} messages...`);

  try {
    const response = await fetch(`${API_SERVER}/api/newtype/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: messageBuffer })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();
    lastAnalysis = Date.now();

    // 이전 상태와 비교
    const prevMood = currentAtmosphere.mood;
    const prevHighlight = currentAtmosphere.is_highlight;

    // 상태 업데이트
    currentAtmosphere = {
      ...result,
      timestamp: Date.now()
    };

    console.log(`[Newtype] Analysis result:`, currentAtmosphere);

    // 분위기 변화 이벤트
    if (result.mood !== prevMood && game.newtype.onAtmosphereChange) {
      game.newtype.onAtmosphereChange(currentAtmosphere, prevMood);
    }

    // 하이라이트 감지 이벤트
    if (result.is_highlight && result.intensity >= CONFIG.HIGHLIGHT_THRESHOLD) {
      console.log(`[Newtype] 🎬 Highlight detected!`);
      ui.notifications.info(`🎬 하이라이트 감지! (${result.mood}, ${result.intensity}%)`);

      if (game.newtype.onHighlight) {
        game.newtype.onHighlight(currentAtmosphere);
      }
    }

    // 버퍼 일부 유지 (연속성)
    messageBuffer = messageBuffer.slice(-5);

  } catch (error) {
    console.error(`[Newtype] Analysis error:`, error);
  }
}

function startEngine() {
  if (engineRunning) return;

  engineRunning = true;
  messageBuffer = [];
  lastAnalysis = Date.now();

  console.log('[Newtype] Engine started');
  ui.notifications.info('🎭 Newtype Engine 시작');

  updateButtonState(true);
}

function stopEngine() {
  if (!engineRunning) return;

  engineRunning = false;
  messageBuffer = [];

  console.log('[Newtype] Engine stopped');
  ui.notifications.info('🎭 Newtype Engine 정지');

  updateButtonState(false);
}

// ============================================================================
// UI - Chat Button
// ============================================================================

let newtypeButton = null;

Hooks.on('renderChatLog', (app, html) => {
  const $html = html instanceof jQuery ? html : $(html);

  // 이미 버튼 있으면 스킵
  if ($html.find('.newtype-btn').length > 0) return;

  // 버튼 생성
  newtypeButton = $('<button class="newtype-btn" type="button"></button>');
  newtypeButton.append('<i class="fas fa-brain"></i>');
  newtypeButton.attr('title', 'Newtype Engine (실시간 분위기 감지)');

  newtypeButton.css({
    'width': '28px',
    'height': '28px',
    'margin-left': '4px',
    'padding': '0',
    'border': '1px solid var(--color-border-light-tertiary)',
    'border-radius': '3px',
    'background': 'var(--color-bg-btn)',
    'cursor': 'pointer',
    'display': 'flex',
    'align-items': 'center',
    'justify-content': 'center',
    'flex': '0 0 28px',
    'color': 'var(--color-text-primary)'
  });

  // 클릭 핸들러
  newtypeButton.on('click', () => {
    if (engineRunning) {
      stopEngine();
    } else {
      startEngine();
    }
  });

  // Chat form에 추가
  let chatForm = $html.find('#chat-form');
  if (chatForm.length === 0) chatForm = $html.find('form.chat-form');
  if (chatForm.length === 0) chatForm = $html.find('[id*="chat"] form');

  if (chatForm.length > 0) {
    chatForm.append(newtypeButton);
    console.log('[Newtype] Button added to chat');
  }
});

function updateButtonState(running) {
  if (!newtypeButton) return;

  if (running) {
    newtypeButton.css({
      'background': '#7c3aed',  // 보라색
      'color': '#ffffff'
    });
    newtypeButton.find('i').addClass('fa-spin');
  } else {
    newtypeButton.css({
      'background': 'var(--color-bg-btn)',
      'color': 'var(--color-text-primary)'
    });
    newtypeButton.find('i').removeClass('fa-spin');
  }
}

export { MODULE_ID };
